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
import bmesh
from mathutils import Vector, Matrix, Quaternion
from math import radians

from . import jsonutils, drivers, bones, utils, vars

# these must be floats
BASE_COLLISION_RADIUS = 0.015
MARGIN = BASE_COLLISION_RADIUS * 2.0 / 3.0
MASS = 5.0 #0.5
STIFFNESS = 1.0
DAMPENING = 0.5
LIMIT = 1.0
ANGLE_RANGE = 120.0
LINEAR_LIMIT = 0.001
CURVE = 1.0
INFLUENCE = 1.0
UPSCALE = 5.0

COLLIDER_PREFIX = "COLLIDER"
COLLIDER_COLLECTION_NAME = "Rigid Body Colliders"


def init_rigidbody_world():
    if not bpy.context.scene.rigidbody_world or not bpy.context.scene.rigidbody_world.enabled:
        try:
            bpy.ops.rigidbody.world_add()
        except: ...
    if "RigidBodyWorld" not in bpy.data.collections:
        bpy.data.collections.new("RigidBodyWorld")
    if "RigidBodyConstraints" not in bpy.data.collections:
        bpy.data.collections.new("RigidBodyConstraints")
    if bpy.context.scene.rigidbody_world.collection is None:
        collection_world = bpy.data.collections["RigidBodyWorld"]
        bpy.context.scene.rigidbody_world.collection = collection_world
    if bpy.context.scene.rigidbody_world.constraints is None:
        collection_constraints = bpy.data.collections["RigidBodyConstraints"]
        bpy.context.scene.rigidbody_world.constraints = collection_constraints
    bpy.context.scene.rigidbody_world.time_scale = 1.0
    if bpy.context.scene.rigidbody_world.substeps_per_frame < 10:
        bpy.context.scene.rigidbody_world.substeps_per_frame = 10
    if bpy.context.scene.rigidbody_world.solver_iterations < 100:
        bpy.context.scene.rigidbody_world.solver_iterations = 100


def add_body_node(co, name,
                  enabled = True,
                  parent_object = None,
                  location_target = None,
                  location_sub_target = None,
                  kinematic = False,
                  passive = False,
                  mass_driver = True,
                  dampening_driver = True, dampening_fac = 1.0,
                  radius_driver = True):

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions = 1, radius = UPSCALE * BASE_COLLISION_RADIUS,
                                          enter_editmode = False,
                                          align = 'WORLD', location = co)

    body_node = utils.get_active_object()
    body_node.hide_render = True
    body_node.scale = (1.0/UPSCALE, 1.0/UPSCALE, 1.0/UPSCALE)
    body_node.name = utils.unique_name(name)

    # add rigid body
    bpy.ops.rigidbody.object_add()
    body_node.rigid_body.collision_shape = 'SPHERE'
    body_node.rigid_body.type = "PASSIVE" if passive else "ACTIVE"
    body_node.rigid_body.enabled = enabled
    body_node.rigid_body.mass = MASS
    body_node.rigid_body.kinematic = kinematic
    body_node.rigid_body.use_margin = True
    body_node.rigid_body.collision_margin = MARGIN
    body_node.rigid_body.linear_damping = 0.9
    body_node.rigid_body.angular_damping = 0.9
    body_node.rigid_body.friction = 0
    body_node.rigid_body.restitution = 0
    #body_node.rigid_body.collision_margin = margin
    if parent_object:
        body_node.location = co
        body_node.parent = parent_object
        body_node.matrix_parent_inverse = parent_object.matrix_world.inverted()

    if location_target:
        c : bpy.types.CopyTransformsConstraint = body_node.constraints.new(type="COPY_TRANSFORMS")
        c.target = location_target
        c.subtarget = location_sub_target
        c.head_tail = 0
        c.mix_mode = "REPLACE"
        c.influence = 1.0

    if mass_driver:
        mass_expr = f"mass"
        driver = drivers.make_driver(body_node.rigid_body, "mass", "SCRIPTED", mass_expr)
        drivers.make_driver_var(driver, "SINGLE_PROP", "mass", parent_object,
                                data_path = f"[\"rigid_body_mass\"]")

    if radius_driver:
        # sphere colliders use embedded margins (i.e. the margin shrinks the radius)
        #radius_expr = f"(radius / {UPSCALE * BASE_COLLISION_SIZE})"
        #for i in range(0, 3):
        #    driver = drivers.make_driver(body_node, "scale", "SCRIPTED", radius_expr, index=i)
        #    drivers.make_driver_var(driver, "SINGLE_PROP", "radius", parent_object,
        #                            data_path = f"[\"rigid_body_radius\"]")
        margin_expr = f"margin"
        driver = drivers.make_driver(body_node.rigid_body, "collision_margin", "SCRIPTED",
                                     margin_expr)
        drivers.make_driver_var(driver, "SINGLE_PROP", "margin", parent_object,
                                    data_path = f"[\"rigid_body_margin\"]")


    if dampening_driver:
        # L + (1 - L)t
        expr_limit = "(1.0 - (1.0 / pow(10.0, limit)))"
        expr_fac = f"pow({dampening_fac}, curve)"
        dampening_expr = f"({expr_limit} * (1.0 - {expr_fac})) + (1.0 * {expr_fac})"

        driver = drivers.make_driver(body_node.rigid_body, "linear_damping", "SCRIPTED",
                                     dampening_expr)
        drivers.make_driver_var(driver, "SINGLE_PROP", "limit", parent_object,
                                data_path = f"[\"rigid_body_limit\"]")
        drivers.make_driver_var(driver, "SINGLE_PROP", "curve", parent_object,
                                data_path = f"[\"rigid_body_curve\"]")

        driver = drivers.make_driver(body_node.rigid_body, "angular_damping", "SCRIPTED",
                                     dampening_expr)
        drivers.make_driver_var(driver, "SINGLE_PROP", "limit", parent_object,
                                data_path = f"[\"rigid_body_limit\"]")
        drivers.make_driver_var(driver, "SINGLE_PROP", "curve", parent_object,
                                data_path = f"[\"rigid_body_curve\"]")


    return body_node


def connect_spring(arm, prefix, bone_name, head_body, tail_body,
                   parent_object = None,
                   use_linear_limit = True,
                   use_angular_limit = True, angular_limit_fac = 1.0,
                   use_linear_spring = False,
                   use_angular_spring = True,
                   dampening_driver = True,
                   stiffness_driver = True,
                   influence_driver = True,
                   angular_limit_driver = True):

    # add an empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', radius = BASE_COLLISION_RADIUS * 1.5, location=head_body.location)
    constraint_object = utils.get_active_object()
    constraint_object.hide_render = True
    if parent_object:
        constraint_object.location = head_body.location
        constraint_object.parent = head_body
        constraint_object.matrix_parent_inverse = head_body.matrix_world.inverted()

    constraint_object.name = utils.unique_name(f"{prefix}_{bone_name}_Spring")
    # add rigid body constraint
    bpy.ops.rigidbody.constraint_add()
    # configure constraint
    rbc = constraint_object.rigid_body_constraint
    rbc.type = 'GENERIC_SPRING'
    rbc.enabled = True
    rbc.disable_collisions = True
    rbc.object1 = head_body
    rbc.object2 = tail_body

    if use_linear_limit:
        rbc.use_limit_lin_x = True
        rbc.use_limit_lin_y = True
        rbc.use_limit_lin_z = True
        rbc.limit_lin_x_lower = -LINEAR_LIMIT
        rbc.limit_lin_y_lower = -LINEAR_LIMIT
        rbc.limit_lin_z_lower = -LINEAR_LIMIT
        rbc.limit_lin_x_upper = LINEAR_LIMIT
        rbc.limit_lin_y_upper = LINEAR_LIMIT
        rbc.limit_lin_z_upper = LINEAR_LIMIT
    else:
        rbc.use_limit_lin_x = False
        rbc.use_limit_lin_y = False
        rbc.use_limit_lin_z = False

    if use_angular_limit:
        rbc.use_limit_ang_x = True
        rbc.use_limit_ang_y = True
        rbc.use_limit_ang_z = True
        rbc.limit_ang_x_lower = -ANGLE_RANGE * 0.008726645
        rbc.limit_ang_y_lower = -ANGLE_RANGE * 0.008726645
        rbc.limit_ang_z_lower = -ANGLE_RANGE * 0.008726645
        rbc.limit_ang_x_upper = ANGLE_RANGE * 0.008726645
        rbc.limit_ang_y_upper = ANGLE_RANGE * 0.008726645
        rbc.limit_ang_z_upper = ANGLE_RANGE * 0.008726645
    else:
        rbc.use_limit_ang_x = False
        rbc.use_limit_ang_y = False
        rbc.use_limit_ang_z = False

    if use_angular_spring:
        rbc.use_spring_ang_x = True
        rbc.use_spring_ang_y = True
        rbc.use_spring_ang_z = True
        rbc.spring_damping_ang_x = DAMPENING
        rbc.spring_damping_ang_y = DAMPENING
        rbc.spring_damping_ang_z = DAMPENING
        rbc.spring_stiffness_ang_x = STIFFNESS
        rbc.spring_stiffness_ang_y = STIFFNESS
        rbc.spring_stiffness_ang_z = STIFFNESS
    else:
        rbc.use_spring_ang_x = False
        rbc.use_spring_ang_y = False
        rbc.use_spring_ang_z = False

    if use_linear_spring:
        rbc.use_spring_x = True
        rbc.use_spring_y = True
        rbc.use_spring_z = True
        rbc.spring_damping_x = DAMPENING
        rbc.spring_damping_y = DAMPENING
        rbc.spring_damping_z = DAMPENING
        rbc.spring_stiffness_x = STIFFNESS
        rbc.spring_stiffness_y = STIFFNESS
        rbc.spring_stiffness_z = STIFFNESS
    else:
        rbc.use_spring_x = False
        rbc.use_spring_y = False
        rbc.use_spring_z = False

    #rbc.spring_type = 'SPRING1'
    # add pose bone constraint to stretch to tail_body
    pose_bone : bpy.types.PoseBone = arm.pose.bones[bone_name]
    c : bpy.types.StretchToConstraint = pose_bone.constraints.new(type="STRETCH_TO")
    c.name = utils.unique_name("Spring_StretchTo")
    c.target = tail_body
    c.influence = INFLUENCE
    c.rest_length = (parent_object.matrix_world.inverted() @ tail_body.location -
                     parent_object.matrix_world.inverted() @ head_body.location).length

    if dampening_driver:

        if use_linear_spring:
            dampening_props = ["spring_damping_x", "spring_damping_y", "spring_damping_z"]
            for prop in dampening_props:
                driver = drivers.make_driver(rbc, prop, "SUM")
                drivers.make_driver_var(driver, "SINGLE_PROP", "dampening", parent_object,
                                        data_path = f"[\"rigid_body_dampening\"]")

        if use_angular_spring:
            dampening_props = ["spring_damping_ang_x", "spring_damping_ang_y", "spring_damping_ang_z"]
            for prop in dampening_props:
                driver = drivers.make_driver(rbc, prop, "SUM")
                drivers.make_driver_var(driver, "SINGLE_PROP", "dampening", parent_object,
                                        data_path = f"[\"rigid_body_dampening\"]")

    if stiffness_driver:

        if use_linear_spring:
            stiffness_props = ["spring_stiffness_x", "spring_stiffness_y", "spring_stiffness_z"]
            for prop in stiffness_props:
                driver = drivers.make_driver(rbc, prop, "SUM")
                drivers.make_driver_var(driver, "SINGLE_PROP", "stiffnes", parent_object,
                                        data_path = f"[\"rigid_body_stiffness\"]")

        if use_angular_spring:
            stiffness_props = ["spring_stiffness_ang_x", "spring_stiffness_ang_y", "spring_stiffness_ang_z"]
            for prop in stiffness_props:
                driver = drivers.make_driver(rbc, prop, "SUM")
                drivers.make_driver_var(driver, "SINGLE_PROP", "stiffnes", parent_object,
                                        data_path = f"[\"rigid_body_stiffness\"]")

    if angular_limit_driver and use_angular_limit:
        ang_limit_props = ["limit_ang_x_lower", "limit_ang_y_lower", "limit_ang_z_lower",
                           "limit_ang_x_upper", "limit_ang_y_upper", "limit_ang_z_upper"]
        for prop in ang_limit_props:
            if "lower" in prop:
                expr = f"-limit * 0.008726645 * pow({angular_limit_fac}, curve)"
            else:
                expr = f"limit * 0.008726645 * pow({angular_limit_fac}, curve)"
            driver = drivers.make_driver(rbc, prop, "SCRIPTED", expr)
            drivers.make_driver_var(driver, "SINGLE_PROP", "limit", parent_object,
                                    data_path = f"[\"rigid_body_angle_limit\"]")
            drivers.make_driver_var(driver, "SINGLE_PROP", "curve", parent_object,
                                    data_path = f"[\"rigid_body_curve\"]")

    if influence_driver:
        driver = drivers.make_driver(c, "influence", "SUM")
        drivers.make_driver_var(driver, "SINGLE_PROP", "influence", parent_object,
                                data_path = f"[\"rigid_body_influence\"]")

    return


def connect_fixed(arm, bone_name, head_body, tail_body, parent_object, copy_location = True, size = 0.075):
    # add an empty
    bpy.ops.object.empty_add(type='CIRCLE', align='WORLD', location=head_body.location, radius = size)
    constraint_object = utils.get_active_object()
    constraint_object.hide_render = True
    if parent_object:
        constraint_object.parent = head_body
        constraint_object.location = Vector((0,0,0))
    # add rigid body constraint
    bpy.ops.rigidbody.constraint_add()
    # configure constraint
    rbc = constraint_object.rigid_body_constraint
    rbc.type = 'FIXED'
    rbc.object1 = head_body
    rbc.object2 = tail_body
    rbc.enabled = True
    rbc.disable_collisions = True
    return

def build_bone_map(arm, edit_bone : bpy.types.EditBone, bone_map : dict = None, length = 0, rigified = False):

    if bone_map is None:
        bone_map = {}

    if length > 0 and rigified:
        # for rigified spring rigs, we only want to use the SIM bones (and the spring rig root)
        if not edit_bone.name.startswith("SIM-"):
            return False

    index = len(bone_map)

    head = arm.matrix_world @ edit_bone.head
    tail = arm.matrix_world @ edit_bone.tail
    length += (head - tail).length

    mapping = { "index": index,
                "head": head,
                "tail": tail,
                "length": length,
                "total": 0,
                "fac": 0,
                "parent": None,
                "children": None,
                "head_body": None,
                "tail_body": None}

    if edit_bone.parent and edit_bone.parent.name in bone_map:
        mapping["parent"] = edit_bone.parent.name

    bone_map[edit_bone.name] = mapping

    children = []
    for child_bone in edit_bone.children:
        if build_bone_map(arm, child_bone, bone_map, length, rigified):
            children.append(child_bone.name)

    mapping["children"] = children

    # if end of chain, calculate the length factors
    if not children:
        total = length
        up = edit_bone
        while up.name in bone_map:
            if total > bone_map[up.name]["total"]:
                bone_map[up.name]["total"] = total
                bone_map[up.name]["fac"] = bone_map[up.name]["length"] / total
            if up.parent:
                up = up.parent
            else:
                break

    return True


def remove_existing_rigid_body_system(arm, rig_prefix, spring_rig_bone_name):

    if not arm:
        return None

    pose_position = arm.data.pose_position
    arm.data.pose_position = "REST"

    rigid_body_system_name = get_rigid_body_system_name(arm, rig_prefix)
    settings = None

    DRIVER_PROPS = [
        "mass", "collision_margin", "linear_damping", "angular_damping", "influence",
        "spring_damping_ang_x", "spring_damping_ang_y", "spring_damping_ang_z",
        "spring_damping_x", "spring_damping_y", "spring_damping_z",
        "spring_stiffness_ang_x", "spring_stiffness_ang_y", "spring_stiffness_ang_z",
        "spring_stiffness_x", "spring_stiffness_y", "spring_stiffness_z",
        "limit_ang_x_lower", "limit_ang_y_lower", "limit_ang_z_lower",
        "limit_ang_x_upper", "limit_ang_y_upper", "limit_ang_z_upper",
        ]

    to_delete = []
    for obj in bpy.data.objects:
        if vars.NODE_PREFIX in obj.name and rigid_body_system_name in obj.name:
            utils.log_info(f"Found Rigid Body System: {obj.name}")
            utils.log_info(f"   Removing drivers...")
            for child in obj.children:
                if child.rigid_body:
                    for prop in DRIVER_PROPS:
                        child.rigid_body.driver_remove(prop)
                if child.rigid_body_constraint:
                    for prop in DRIVER_PROPS:
                        child.rigid_body_constraint.driver_remove(prop)
            to_delete.append(obj)
            if not settings:
                settings = {
                    "rigid_body_influence": obj["rigid_body_influence"],
                    "rigid_body_limit": obj["rigid_body_limit"],
                    "rigid_body_curve": obj["rigid_body_curve"],
                    "rigid_body_mass": obj["rigid_body_mass"],
                    "rigid_body_dampening": obj["rigid_body_dampening"],
                    "rigid_body_stiffness": obj["rigid_body_stiffness"],
                    "rigid_body_margin": obj["rigid_body_margin"],
                    "rigid_body_angle_limit": obj["rigid_body_angle_limit"],
                }

    utils.log_indent()

    remove_constraints = []
    utils.log_info(f"Removing bone constraints and drivers...")
    for bone in arm.pose.bones:
        c : bpy.types.StretchToConstraint
        for c in bone.constraints:
            if c.type == "STRETCH_TO":
                if vars.NODE_PREFIX in c.name and "Spring_StretchTo" in c.name:
                    #utils.log_info(f"Removing Bone Constraint: {c.name} from {bone.name}")
                    c.driver_remove("influence")
                    remove_constraints.append([bone, c])
    for bone, c in remove_constraints:
        bone.constraints.remove(c)

    for obj in to_delete:
        if utils.object_exists(obj):
            utils.log_info(f"Removing Rigid Body System: {obj.name}")
            utils.delete_object_tree(obj)

    utils.log_recess()

    set_rigify_simulation_influence(arm, spring_rig_bone_name, 0.0, 1.0)

    arm.data.pose_position = pose_position

    return settings


def add_rigid_body_system(arm, parent_bone_name, rig_prefix, settings = None):
    rigid_body_system_name = get_rigid_body_system_name(arm, rig_prefix)
    bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD', location=(0,0,0))
    rigid_body_system = utils.get_active_object()
    rigid_body_system.hide_render = True
    rigid_body_system.parent = arm
    rigid_body_system.parent_type = "BONE"
    rigid_body_system.parent_bone = parent_bone_name
    rigid_body_system.location = Vector((0,0,0))
    rigid_body_system.name = utils.unique_name(rigid_body_system_name)


    if settings:
        # these aren't declared global so it shouldn't overwrite them permamently...
        influence = settings["rigid_body_influence"]
        limit = settings["rigid_body_limit"]
        curve = settings["rigid_body_curve"]
        mass = settings["rigid_body_mass"]
        dampening = settings["rigid_body_dampening"]
        stiffness = settings["rigid_body_stiffness"]
        margin = settings["rigid_body_margin"]
        angle_limit = settings["rigid_body_angle_limit"]
    else:
        influence = INFLUENCE
        limit = LIMIT
        curve = CURVE
        mass = MASS
        dampening = DAMPENING
        stiffness = STIFFNESS
        margin = MARGIN
        angle_limit = ANGLE_RANGE

    drivers.add_custom_float_property(rigid_body_system, "rigid_body_influence", influence, 0.0, 1.0,
                                      description = "How much of the simulation is copied into the pose bones")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_limit", limit, 0.0, 4.0,
                                      description = "How much to restrain the overall movement of the rigid body simulation")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_curve", curve, 1.0/8.0, 8.0, 1.0/8.0, 2.0,
                                      description = "The dampening curve factor along the length of the spring bone chains. Less curve gives more movement near the roots")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_mass", mass, 0.0, 100.0, 0.1, 10.0,
                                      description = "Mass of the rigid body particles representing the bones. More mass, more inertia")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_dampening", dampening, 0.0, 10000.0, 0.0, 10.0,
                                      description = "Spring dampening, how quickly the hair movement slows down.")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_stiffness", stiffness, 0.0, 10000.0, 0.0, 100.0,
                                      description = "Spring stiffness, how resistant to movement.")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_margin", margin, 0.0, 1.0, 0.001, BASE_COLLISION_RADIUS,
                                      description = "Collision margin. How far into the surface to be considered a collision.")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_angle_limit", angle_limit, 0.0, 360.0, 0.0, 120.0,
                                      description = "Angular limit of movement")

    return rigid_body_system


def is_rigid_body(chr_cache, obj):
    if chr_cache and obj:
        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        if proxy:
            obj = proxy
    return obj and obj.rigid_body is not None


def get_rigid_body(chr_cache, obj):
    if chr_cache and obj:
        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        if proxy:
            obj = proxy
        return obj.rigid_body
    return None


def enable_rigid_body_collision_mesh(chr_cache, obj):
    arm = None
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            pose_position = arm.data.pose_position
            arm.data.pose_position = "REST"

        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        if proxy:
            if obj.rigid_body:
                # if there is a collision body proxy but
                # there is a rigid body mod on the real body, remove it:
                utils.set_active_object(obj)
                hidden = False
                if not obj.visible_get():
                    hidden = True
                    utils.unhide(obj)
                bpy.ops.rigidbody.object_remove()
                if hidden:
                    utils.hide(obj)
            obj = proxy

    if obj.rigid_body is None:
        utils.set_active_object(obj)
        hidden = False
        if not obj.visible_get():
            hidden = True
            utils.unhide(obj)
        bpy.ops.rigidbody.object_add()
        if hidden:
            utils.hide(obj)

    obj.rigid_body.collision_shape = 'MESH'
    obj.rigid_body.type = "PASSIVE"
    obj.rigid_body.enabled = True
    obj.rigid_body.mass = 1.0
    obj.rigid_body.kinematic = True
    obj.rigid_body.use_margin = True
    obj.rigid_body.mesh_source = 'DEFORM'
    obj.rigid_body.use_deform = True
    obj.rigid_body.friction = 0
    obj.rigid_body.restitution = 0
    obj.rigid_body.collision_margin = MARGIN
    obj.rigid_body.linear_damping = 0
    obj.rigid_body.angular_damping = 0

    if arm:
        arm.data.pose_position = pose_position


def disable_rigid_body_collision_mesh(chr_cache, obj):
    arm = None
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            pose_position = arm.data.pose_position
            arm.data.pose_position = "REST"

        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        if proxy:
            if obj.rigid_body:
                utils.set_active_object(obj)
                hidden = False
                if not obj.visible_get():
                    hidden = True
                    utils.unhide(obj)
                bpy.ops.rigidbody.object_remove()
                if hidden:
                    utils.hide(obj)
            obj = proxy

    if obj.rigid_body is not None:
        utils.set_active_object(obj)
        hidden = False
        if not obj.visible_get():
            hidden = True
            utils.unhide(obj)
        bpy.ops.rigidbody.object_remove()
        if hidden:
            utils.hide(obj)

    if arm:
        arm.data.pose_position = pose_position


def get_rigid_body_system_name(arm, rig_prefix):
    return f"{arm.name}_{rig_prefix}_RigidBody"


def get_spring_rigid_body_system(arm, rig_prefix):
    if arm:
        rigid_body_system_name = get_rigid_body_system_name(arm, rig_prefix)
        for obj in bpy.data.objects:
            if vars.NODE_PREFIX in obj.name and rigid_body_system_name in obj.name:
                return obj
    return None


def build_spring_rigid_body_system(chr_cache, spring_rig_prefix, spring_rig_bone_name, settings = None):
    props = vars.props()

    arm = chr_cache.get_armature()
    if not arm or spring_rig_bone_name not in arm.data.bones:
        return False

    pose_position = arm.data.pose_position
    arm.data.pose_position = "REST"

    spring_rig_bone = arm.pose.bones[spring_rig_bone_name]
    rigified = "rigified" in spring_rig_bone and spring_rig_bone["rigified"]

    # generate a map of the spring rig bones
    if not utils.edit_mode_to(arm):
        return
    root_bone = arm.data.edit_bones[spring_rig_bone_name]

    # fix old spring rig bone name
    if spring_rig_bone_name.startswith("RL_"):
        root_bone.name = "RLS_" + spring_rig_bone_name[3:]
        spring_rig_bone_name = root_bone.name
        utils.log_info(f"Updating spring rig name to {spring_rig_bone_name}")

    bone_map = {}
    build_bone_map(arm, root_bone, rigified = rigified, bone_map = bone_map)
    utils.object_mode_to(arm)

    # remove any existing rig and store it's settings
    rigid_body_system = get_spring_rigid_body_system(arm, spring_rig_prefix)
    if rigid_body_system:
        if not settings:
            settings = remove_existing_rigid_body_system(arm, spring_rig_prefix, spring_rig_bone_name)
        else:
            remove_existing_rigid_body_system(arm, spring_rig_prefix, spring_rig_bone_name)

    # create a new spring rig
    utils.log_info(f"Building Rigid Body System from: {spring_rig_bone_name}")
    rigid_body_system = add_rigid_body_system(arm, spring_rig_bone_name, spring_rig_prefix, settings)

    # add the root node for the spring rig
    root_body = add_body_node(bone_map[spring_rig_bone_name]["head"],
                              parent_object=rigid_body_system,
                              name = f"{spring_rig_prefix}_{spring_rig_bone_name}",
                              enabled = False, kinematic = True, passive = True,
                              #location_target = arm, location_sub_target = spring_rig_bone_name,
                              dampening_driver = False, mass_driver = False, radius_driver = False)

    # from the bone map, generate the rigid body nodes and their spring constraints
    for bone_name in bone_map:

        if bone_name == spring_rig_bone_name:
            continue

        mapping = bone_map[bone_name]
        parent_name = mapping["parent"]

        # anything connected to the rig bone is fixed in place, these are the roots of the bone chains
        if parent_name == spring_rig_bone_name:
            head_body = add_body_node(mapping["head"], name = f"{spring_rig_prefix}_{bone_name}_Head",
                                      parent_object = rigid_body_system)
            mapping["head_body"] = head_body
            connect_fixed(arm, bone_name, root_body, head_body, parent_object = rigid_body_system)

        # child bones of a bone chain, connect the tail_body of the parent to the tail_body for this bone
        else:
            parent_mapping = bone_map[parent_name]
            head_body = parent_mapping["tail_body"]
            if not head_body:
                dampening_fac = 1.0 - parent_mapping["fac"]
                head_body = add_body_node(parent_mapping["tail"], name = f"{spring_rig_prefix}_{parent_name}_Tail",
                                          parent_object = rigid_body_system, dampening_fac = dampening_fac)
                parent_mapping["tail_body"] = head_body

        # add the tail node rigid body
        fac = mapping["fac"]
        dampening_fac = 1.0 - fac
        tail_body = add_body_node(mapping["tail"], name = f"{spring_rig_prefix}_{bone_name}_Tail",
                                  parent_object = rigid_body_system, dampening_fac = dampening_fac)

        mapping["head_body"] = head_body
        mapping["tail_body"] = tail_body

        # connect the head and the tail together with a generic spring constraint
        connect_spring(arm, spring_rig_prefix, bone_name, head_body, tail_body,
                       parent_object = rigid_body_system,
                       use_angular_spring=True,
                       use_linear_spring=False,
                       use_angular_limit=True, angular_limit_fac = fac,
                       use_linear_limit=True,
                       )

    set_rigify_simulation_influence(arm, spring_rig_bone_name, 1.0, 1.0)

    init_rigidbody_world()

    collections = utils.get_object_scene_collections(arm)
    system_objects = utils.get_object_tree(rigid_body_system)
    for obj in system_objects:
        utils.move_object_to_scene_collections(obj, collections)
        utils.hide(obj)

    arm.data.pose_position = pose_position


def set_rigify_simulation_influence(arm, spring_rig_bone_name, sim_value, ik_fk_value):
    # activate the simulation constraint influence
    if arm and spring_rig_bone_name in arm.pose.bones:
        spring_rig_bone = arm.pose.bones[spring_rig_bone_name]
        child_bones = bones.get_bone_children(spring_rig_bone, include_root=False)
        for child_bone in child_bones:
            if "SIM" in child_bone:
                child_bone["SIM"] = sim_value
            if "IK_FK" in child_bone:
                child_bone["IK_FK"] = ik_fk_value


def add_simulation_bone_collection(arm):
    if utils.B400():
        if "Simulation" not in arm.data.collections:
            arm.data.collections.new("Simulation")
    else:
        if "Simulation" not in arm.pose.bone_groups:
            bone_group = arm.pose.bone_groups.new(name="Simulation")
            bone_group.color_set = "THEME02"


def reset_cache(context):

    if bpy.context.scene.use_preview_range:
        start = bpy.context.scene.frame_preview_start
        end = bpy.context.scene.frame_preview_end
    else:
        start = bpy.context.scene.frame_start
        end = bpy.context.scene.frame_end

    rigidbody_world = bpy.context.scene.rigidbody_world
    if rigidbody_world:
        cache = rigidbody_world.point_cache

        # free the bake
        if cache.is_baked:
            utils.log_info("Freeing baked point cache...")
            context_override = {"point_cache": bpy.context.scene.rigidbody_world.point_cache}
            bpy.ops.ptcache.free_bake(context_override)

        # invalidate the cache
        utils.log_info("Invalidating point cache...")
        steps = 10
        interations = rigidbody_world.solver_iterations
        if cache:
            cache.frame_start = 1
            cache.frame_end = 1
        try:
            steps = rigidbody_world.steps_per_second
            rigidbody_world.steps_per_second = 1
        except:
            pass
        try:
            steps = rigidbody_world.substeps_per_frame
            rigidbody_world.substeps_per_frame = 1
        except:
            pass
        rigidbody_world.solver_iterations = 1

        # reset the cache
        utils.log_info("Setting rigid body world bake cache frame range to [" + str(start) + " - " + str(end) + "]")
        if cache:
            cache.frame_start = start
            cache.frame_end = end
        try:
            rigidbody_world.steps_per_second = steps
        except:
            pass
        try:
            rigidbody_world.substeps_per_frame = steps
        except:
            pass
        rigidbody_world.solver_iterations = interations


def create_capsule_collider(name, location, rotation, scale, radius, length, axis):
    bm = bmesh.new()
    try:
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=9, radius=radius)
    except:
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=9, diameter=radius)
    bm.verts.ensure_lookup_table()

    i = 2
    for vert in bm.verts:
        if vert.co[i] < 0:
            vert.co[i] -= length * 0.5
        elif vert.co[i] > 0:
            vert.co[i] += length * 0.5

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(object)
    object.display_type = 'WIRE'

    object.location = location
    object.rotation_mode = "QUATERNION"
    r = Quaternion()
    r.identity()
    if axis == "X":
        mat_rot_y = Matrix.Rotation(radians(90), 4, 'Y')
        mat_rot_z = Matrix.Rotation(radians(90), 4, 'Z')
        r.rotate(mat_rot_z)
        r.rotate(mat_rot_y)
    if axis == "Y":
        mat_rot_x = Matrix.Rotation(radians(90), 4, 'X')
        mat_rot_z = Matrix.Rotation(radians(90), 4, 'Z')
        r.rotate(mat_rot_z)
        r.rotate(mat_rot_x)

    r.rotate(rotation)
    object.rotation_quaternion = r
    object.scale = scale
    return object


def create_sphere_collider(name, location, rotation, scale, radius):
    bm = bmesh.new()
    try:
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=9, radius=radius)
    except:
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=9, diameter=radius)
    bm.verts.ensure_lookup_table()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(object)
    object.display_type = 'WIRE'

    object.location = location
    object.rotation_mode = "QUATERNION"
    r = Quaternion()
    r.identity()
    r.rotate(rotation)
    object.rotation_quaternion = r
    object.scale = scale
    return object


def create_box_collider(name, location, rotation, scale, extents, axis):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.verts.ensure_lookup_table()

    for vert in bm.verts:
        for i, extent in enumerate(extents):
            if vert.co[i] < 0:
                vert.co[i] = -extent
            elif vert.co[i] > 0:
                vert.co[i] = extent

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    object = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(object)
    object.display_type = 'WIRE'

    object.location = location
    object.rotation_mode = "QUATERNION"
    object.rotation_quaternion = rotation
    object.scale = scale
    return object


def fix_quat(q):
    return [q[3], q[0], q[1], q[2]]

def unfix_quat(q):
    return [q[1], q[2], q[3], q[0]]


def build_rigid_body_colliders(chr_cache, json_data, first_import = False, bone_mapping = None):
    physics_json = None
    if json_data:
        chr_json = jsonutils.get_character_json(json_data, chr_cache.get_character_id())
        physics_json = jsonutils.get_physics_json(chr_json)

    if not chr_cache or not json_data or not physics_json:
        utils.log_error("Invalid character data for collider setup!")
        return False

    if "Collision Shapes" not in physics_json:
        utils.log_error("No collision shapes in json data!")
        return False

    arm = chr_cache.get_armature()
    if not arm:
        utils.log_error("No armature in character!")
        return False

    collection = utils.create_collection(COLLIDER_COLLECTION_NAME)
    collection.hide_render = True

    use_bind_data = False
    if not first_import and "Has BindPose Data" in physics_json:
        use_bind_data = True

    utils.object_mode_to(arm)
    arm_settings = bones.store_armature_settings(arm)
    bones.make_bones_visible(arm)

    old_action = utils.safe_get_action(arm)
    old_pose = arm.data.pose_position

    if use_bind_data:
        bones.set_rig_bind_pose(arm)
    else:
        # reset the existing action back to the first frame
        # (the colliders in the json data are posed to the first frame)
        arm.data.pose_position = "POSE"
        bpy.ops.screen.animation_cancel(restore_frame=False)
        bpy.ops.screen.frame_jump(end = False)

    # build and attach the colliders
    collider_cache = []
    utils.set_active_object(arm, True)
    collider_json = physics_json["Collision Shapes"]
    for bone_name in collider_json:
        for shape_name in collider_json[bone_name]:
            target_bone_name = bone_name
            if bone_mapping:
                target_bone_name = bones.get_rigify_meta_bone(arm, bone_mapping, bone_name)
            if target_bone_name not in arm.data.bones:
                continue
            name = f"{COLLIDER_PREFIX}_{bone_name}_{shape_name}"
            shape_data = collider_json[bone_name][shape_name]
            active = shape_data["Bone Active"]
            shape = shape_data["Bound Type"]
            axis = shape_data["Bound Axis"]
            margin = shape_data["Margin"] * 0.01
            friction = shape_data["Friction"]
            elasticity = shape_data["Elasticity"] / 10.0
            translate = Vector(shape_data["WorldTranslate"]) * 0.01
            rotate = Quaternion(fix_quat(shape_data["WorldRotationQ"]))
            scale = shape_data["WorldScale"]
            if use_bind_data:
                translate = Vector(shape_data["BindPose WorldTranslate"]) * 0.01
                rotate = Quaternion(fix_quat(shape_data["BindPose WorldRotationQ"]))
                scale = shape_data["BindPose WorldScale"]
                axis = shape_data["BindPose Bound Axis"]
            obj : bpy.types.Object = None
            if shape == "Box":
                extent = Vector(shape_data["Extent"]) * 0.01 / 2.0
                obj = create_box_collider(name, translate, rotate, scale, extent, axis)
            elif shape == "Capsule":
                radius = shape_data["Radius"] * 0.01
                length = shape_data["Capsule Length"] * 0.01
                obj = create_capsule_collider(name, translate, rotate, scale, radius, length, axis)
            elif shape == "Sphere":
                radius = shape_data["Radius"] * 0.01
                obj = create_sphere_collider(name, translate, rotate, scale, radius)

            if not obj:
                continue

            # using operators to parent because matrix_parent_inverse doesn't work correctly
            if bones.set_active_bone(arm, target_bone_name, deselect_all=True):
                utils.set_active_object(arm, True)
                utils.unhide(obj)
                obj.select_set(True)
                bpy.ops.object.parent_set(type='BONE', keep_transform=True)
            else:
                utils.log_error(f"Unable to parent rigid body collider {obj.name} to armature!")
                utils.delete_mesh_object(obj)
                continue

            if active:
                utils.set_active_object(obj)
                # enable cloth collision
                # NOTE: Disabled, cloth collisions with the primitive colliders is bad...
                if False:
                    collision_mod = obj.modifiers.new(utils.unique_name("Collision"), type="COLLISION")
                    collision_mod.settings.thickness_outer = margin
                    collision_mod.settings.thickness_inner = margin
                    collision_mod.settings.cloth_friction = friction
                    collision_mod.settings.damping = 0.0
                # enable rigid body collision
                bpy.ops.rigidbody.object_add()
                if shape == "Capsule":
                    obj.rigid_body.collision_shape = 'CAPSULE'
                elif shape == "Box":
                    obj.rigid_body.collision_shape = 'BOX'
                obj.rigid_body.type = "PASSIVE"
                obj.rigid_body.kinematic = True
                obj.rigid_body.use_margin = True
                obj.rigid_body.friction = friction
                obj.rigid_body.restitution = elasticity
                obj.rigid_body.collision_margin = margin
                obj.rigid_body.linear_damping = 0
                obj.rigid_body.angular_damping = 0
            utils.move_object_to_scene_collections(obj, [collection])
            utils.hide(obj)
            obj.hide_render = True

            cache = {"bone_name": bone_name, "shape_name": shape_name, "object": obj }
            collider_cache.append(cache)

    # save the bind pose collider transforms to the json data so they can be
    # reconstructed later without needing the original pose:
    if not use_bind_data:

        # set to bind pose
        bones.set_rig_bind_pose(arm)

        # write the bind translation, rotation quaternion, scale and axis of the colliders to the json data
        for cache in collider_cache:
            bone_name = cache["bone_name"]
            shape_name = cache["shape_name"]
            obj = cache["object"]
            shape_data = collider_json[bone_name][shape_name]
            shape_data["BindPose WorldTranslate"] = list(obj.matrix_world.translation * 100.0)
            shape_data["BindPose WorldRotationQ"] = unfix_quat(list(obj.matrix_world.to_quaternion()))
            shape_data["BindPose WorldScale"] = list(obj.scale)
            # bind posed collider data is always in Z axis
            shape_data["BindPose Bound Axis"] = "Z"

        physics_json["Has BindPose Data"] = True

        # write back the updated json data
        chr_cache.write_json_data(json_data)

    # restore the original action
    utils.safe_set_action(arm, old_action)
    arm.data.pose_position = old_pose
    bones.restore_armature_settings(arm, arm_settings)

    return True


def get_rigid_body_colliders(arm):
    colliders = []
    if arm:
        for obj in arm.children:
            if is_rigid_body_collider(obj):
                colliders.append(obj)
    return colliders


def has_rigid_body_colliders(arm):
    obj : bpy.types.Object
    if arm:
        for obj in arm.children:
            if is_rigid_body_collider(obj):
                return True
    return False


def is_rigid_body_collider(obj):
    return utils.object_exists_is_mesh(obj) and obj.name.startswith(COLLIDER_PREFIX)


def get_rigidbody_collider_collection():
    collection = None
    if COLLIDER_COLLECTION_NAME in bpy.data.collections:
        collection = bpy.data.collections[COLLIDER_COLLECTION_NAME]
    return collection


def remove_rigid_body_colliders(arm):
    collection = get_rigidbody_collider_collection()
    colliders = get_rigid_body_colliders(arm)
    for collider in colliders:
        utils.delete_mesh_object(collider)
    if collection and len(collection.objects) == 0:
        bpy.data.collections.remove(collection)


def colliders_visible(arm, colliders = None):
    if not colliders:
        colliders = get_rigid_body_colliders(arm)
    for collider in colliders:
        if not collider.visible_get():
            return False
    return True


def hide_colliders(arm):
    if arm:
        colliders = get_rigid_body_colliders(arm)
        hide_state = colliders_visible(arm, colliders)
        if hide_state:
            toggle_show_colliders(arm)


def toggle_show_colliders(arm):
    colliders = get_rigid_body_colliders(arm)
    hide_state = colliders_visible(arm, colliders)
    layer_collections = utils.get_view_layer_collections(search = COLLIDER_COLLECTION_NAME)
    for collection in layer_collections:
        collection.exclude = False
        collection.hide_viewport = False
    for collider in colliders:
        utils.hide(collider, hide_state)


def convert_colliders_to_rigify(chr_cache, cc3_rig, rigify_rig, bone_mapping):
    obj : bpy.types.Object
    if cc3_rig and rigify_rig:

        utils.object_mode_to(rigify_rig)
        cc3_arm_settings = bones.store_armature_settings(cc3_rig)
        rigify_arm_settings = bones.store_armature_settings(rigify_rig)
        cc3_rig.location = (0,0,0)
        rigify_rig.location = (0,0,0)
        bones.set_rig_bind_pose(cc3_rig)
        bones.set_rig_bind_pose(rigify_rig)
        bones.make_bones_visible(rigify_rig)

        # make sure the colliders can be make visible and selectable
        layer_collections = utils.get_view_layer_collections(search = COLLIDER_COLLECTION_NAME)
        for collection in layer_collections:
            collection.exclude = False
            collection.hide_viewport = False

        colliders = get_rigid_body_colliders(cc3_rig)
        for obj in colliders:
            bone_name = obj.parent_bone
            rigify_bone_name = bones.get_rigify_meta_bone(rigify_rig, bone_mapping, bone_name)

            if rigify_bone_name:
                # using operators to parent because matrix_parent_inverse doesn't work correctly
                utils.set_active_object(rigify_rig, True)
                if bones.set_active_bone(rigify_rig, rigify_bone_name, deselect_all=True):
                    utils.unhide(obj)
                    obj.select_set(True)
                    bpy.ops.object.parent_set(type='BONE', keep_transform=True)
                else:
                    utils.log_error(f"Enable to parent collider object {obj.name} to rigify rig!")
                    utils.delete_mesh_object(obj)
            else:
                utils.log_error(f"Unable to map {bone_name} to rigify bone!")
                utils.delete_mesh_object(obj)

        # hide the colliders
        for obj in colliders:
            if utils.object_exists(obj):
                utils.hide(obj)
        for collection in layer_collections:
            collection.hide_viewport = True

        bones.restore_armature_settings(cc3_rig, cc3_arm_settings)
        bones.restore_armature_settings(rigify_rig, rigify_arm_settings)

