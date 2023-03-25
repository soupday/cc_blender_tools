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
from mathutils import Vector

from . import drivers, bones, utils, vars

# these must be floats
BASE_COLLISION_SIZE = 0.0125
SIZE = 0.0125
MASS = 1.0
STIFFNESS = 50.0
DAMPENING = 1000.0
LIMIT = 1.5
ANGLE_RANGE = 90.0
LINEAR_LIMIT = 0.0
CURVE = 0.75
INFLUENCE = 1.0

def add_body_node(co, name,
                  enabled = True,
                  parent_object = None,
                  location_target = None,
                  location_sub_target = None,
                  kinematic = False,
                  mass_driver = True,
                  dampening_driver = True, dampening_fac = 1.0,
                  radius_driver = True):

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions = 1, radius = BASE_COLLISION_SIZE,
                                          enter_editmode = False,
                                          align = 'WORLD', location = co)

    body_node = bpy.context.active_object
    body_node.name = utils.unique_name(name)

    # add rigid body
    bpy.ops.rigidbody.object_add()
    body_node.rigid_body.collision_shape = 'SPHERE'
    body_node.rigid_body.type = "ACTIVE"
    body_node.rigid_body.enabled = enabled
    body_node.rigid_body.mass = MASS
    body_node.rigid_body.kinematic = kinematic
    body_node.rigid_body.use_margin = True
    body_node.rigid_body.collision_margin = 0.025
    body_node.rigid_body.linear_damping = 0.75
    body_node.rigid_body.angular_damping = 0.75
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
        driver = drivers.make_driver(body_node.rigid_body, "mass", "SUM")
        drivers.make_driver_var(driver, "SINGLE_PROP", "mass", parent_object,
                                data_path = f"[\"rigid_body_mass\"]")

    if radius_driver:
        # sphere colliders use embedded margins (i.e. the margin shrinks the radius)
        margin_expr = f"(radius / {BASE_COLLISION_SIZE})"
        for i in range(0, 3):
            driver = drivers.make_driver(body_node, "scale", "SCRIPTED", margin_expr, index=i)
            drivers.make_driver_var(driver, "SINGLE_PROP", "radius", parent_object,
                                    data_path = f"[\"rigid_body_radius\"]")
        margin_expr = f"(0.5 * radius)"
        driver = drivers.make_driver(body_node.rigid_body, "collision_margin", "SCRIPTED",
                                     margin_expr)
        drivers.make_driver_var(driver, "SINGLE_PROP", "radius", parent_object,
                                    data_path = f"[\"rigid_body_radius\"]")


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
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', radius = BASE_COLLISION_SIZE * 1.5, location=head_body.location)
    constraint_object = bpy.context.active_object
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
                expr = f"-limit * 0.008726645 * {angular_limit_fac}"
            else:
                expr = f"limit * 0.008726645 * {angular_limit_fac}"
            driver = drivers.make_driver(rbc, prop, "SCRIPTED", expr)
            drivers.make_driver_var(driver, "SINGLE_PROP", "limit", parent_object,
                                    data_path = f"[\"rigid_body_angle_limit\"]")

    if influence_driver:
        driver = drivers.make_driver(c, "influence", "SUM")
        drivers.make_driver_var(driver, "SINGLE_PROP", "influence", parent_object,
                                data_path = f"[\"rigid_body_influence\"]")

    return


def connect_fixed(arm, bone_name, head_body, tail_body, parent_object, copy_location = True, size = 0.075):
    # add an empty
    bpy.ops.object.empty_add(type='CIRCLE', align='WORLD', location=head_body.location, radius = size)
    constraint_object = bpy.context.active_object
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
                    "rigid_body_radius": obj["rigid_body_radius"],
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

    set_rigify_simulation_influence(arm, spring_rig_bone_name, 0.0)

    return settings


def add_rigid_body_system(arm, parent_bone_name, rig_prefix, settings = None):
    rigid_body_system_name = get_rigid_body_system_name(arm, rig_prefix)
    bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD', location=(0,0,0))
    rigid_body_system = bpy.context.active_object
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
        size = settings["rigid_body_radius"]
        angle_limit = settings["rigid_body_angle_limit"]
    else:
        influence = INFLUENCE
        limit = LIMIT
        curve = CURVE
        mass = MASS
        dampening = DAMPENING
        stiffness = STIFFNESS
        size = SIZE
        angle_limit = ANGLE_RANGE

    drivers.add_custom_float_property(rigid_body_system, "rigid_body_influence", influence, 0.0, 1.0,
                                      description = "How much of the simulation is copied into the pose bones")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_limit", limit, 0.0, 4.0,
                                      description = "How much to dampen the overall movement of the simulation")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_curve", curve, 1.0/8.0, 2.0,
                                      description = "The dampening curve factor along the length of the spring bone chains. Less curve gives more movement near the roots")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_mass", mass, 0.0, 1.0,
                                      description = "Mass of the rigid body particles representing the bones. More mass, more inertia")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_dampening", dampening, 0.0, 10000.0,
                                      description = "Spring dampening, how quickly the hair slows down.\nThis value only really takes effect at very high limit values")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_stiffness", stiffness, 0.0, 100.0,
                                      description = "Spring stiffness, how resistant to movement.\nThis value only really takes effect at very high limit values")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_radius", size, 0.001, 0.025,
                                      description = "Collision radius of the rigid body particles representing the bones. Note: Too much and the hair will be pushed away from the body")
    drivers.add_custom_float_property(rigid_body_system, "rigid_body_angle_limit", angle_limit, 0, 120,
                                      description = "Angular limit of movement")

    return rigid_body_system


def is_rigid_body(chr_cache, obj):
    if chr_cache and obj:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and obj_cache.object_type == "BODY":
            if utils.object_exists_is_mesh(chr_cache.collision_body):
                obj = chr_cache.collision_body
    return obj and obj.rigid_body is not None


def enable_rigid_body_collision_mesh(chr_cache, obj):
    if chr_cache:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and obj_cache.object_type == "BODY":
            if utils.object_exists_is_mesh(chr_cache.collision_body):
                if obj.rigid_body:
                    utils.set_active_object(obj)
                    hidden = False
                    if not obj.visible_get():
                        hidden = True
                        obj.hide_set(False)
                    bpy.ops.rigidbody.object_remove()
                    if hidden:
                        obj.hide_set(True)
                obj = chr_cache.collision_body

    if obj.rigid_body is None:
        utils.set_active_object(obj)
        hidden = False
        if not obj.visible_get():
            hidden = True
            obj.hide_set(False)
        bpy.ops.rigidbody.object_add()
        if hidden:
            obj.hide_set(True)
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
    obj.rigid_body.collision_margin = 0.025
    obj.rigid_body.linear_damping = 0
    obj.rigid_body.angular_damping = 0


def disable_rigid_body_collision_mesh(chr_cache, obj):
    if chr_cache:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and obj_cache.object_type == "BODY":
            if utils.object_exists_is_mesh(chr_cache.collision_body):
                if obj.rigid_body:
                    utils.set_active_object(obj)
                    hidden = False
                    if not obj.visible_get():
                        hidden = True
                        obj.hide_set(False)
                    bpy.ops.rigidbody.object_remove()
                    if hidden:
                        obj.hide_set(True)
                obj = chr_cache.collision_body

    if obj.rigid_body is not None:
        utils.set_active_object(obj)
        hidden = False
        if not obj.visible_get():
            hidden = True
            obj.hide_set(False)
        bpy.ops.rigidbody.object_remove()
        if hidden:
            obj.hide_set(True)


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
    props = bpy.context.scene.CC3ImportProps

    # TODO: Align the body nodes & constraints with the bone y axis...

    arm = chr_cache.get_armature()
    if not arm or spring_rig_bone_name not in arm.data.bones:
        return False

    spring_rig_bone = arm.pose.bones[spring_rig_bone_name]
    rigified = "rigified" in spring_rig_bone and spring_rig_bone["rigified"]

    # generate a map of the spring rig bones
    utils.edit_mode_to(arm)
    root_bone = arm.data.edit_bones[spring_rig_bone_name]
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
                              enabled = False, kinematic = True,
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
                       use_angular_spring= True, angular_limit_fac = fac,
                       use_linear_spring= False,
                       use_angular_limit= True,
                       use_linear_limit= True,
                       )

    set_rigify_simulation_influence(arm, spring_rig_bone_name, 1.0)
    if bpy.context.scene.rigidbody_world.solver_iterations < 100:
        bpy.context.scene.rigidbody_world.solver_iterations = 100


    utils.hide_tree(rigid_body_system)


def set_rigify_simulation_influence(arm, spring_rig_bone_name, value):
    # activate the simulation constraint influence
    if arm and spring_rig_bone_name in arm.pose.bones:
        spring_rig_bone = arm.pose.bones[spring_rig_bone_name]
        child_bones = bones.get_bone_children(spring_rig_bone, include_root=False)
        for child_bone in child_bones:
            if "SIM" in child_bone:
                child_bone["SIM"] = value


def add_simulation_bone_group(arm):
    if "Simulation" not in arm.pose.bone_groups:
        bone_group = arm.pose.bone_groups.new(name="Simulation")
        bone_group.color_set = "THEME02"


def reset_cache(context):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    arm = chr_cache.get_armature()

    # adjust scene frame range from character armature action range
    # (widen the range if it doesn't cover the armature action)
    action = utils.safe_get_action(arm)
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    if action:
        action_start = math.floor(action.frame_range[0])
        action_end = math.ceil(action.frame_range[1])
        if action_start < start:
            start = action_start
        if action_end > end:
            end = action_end
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end

    # free the bakes
    bpy.ops.ptcache.free_bake_all()
    #
    rigidbody_world = bpy.context.scene.rigidbody_world

    if rigidbody_world:
        cache = rigidbody_world.point_cache

        # invalidate the cache
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
