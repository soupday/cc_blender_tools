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
from mathutils import Vector
from . import rigidbody, utils, bones, vars


HEAD_RIG_NAME = "RLS_Hair_Rig_Head"
JAW_RIG_NAME = "RLS_Hair_Rig_Jaw"
HAIR_BONE_PREFIX = "Hair"
BEARD_BONE_PREFIX = "Beard"
HEAD_BONE_NAMES = ["ORG-spine.006", "CC_Base_Head", "RL_Head", "Head", "head"]
JAW_BONE_NAMES = ["ORG-jaw", "CC_Base_JawRoot", "RL_JawRoot", "JawRoot", "teeth.B"]
EYE_BONE_NAMES = ["ORG-eye.R", "ORG-eye.L", "CC_Base_R_Eye", "CC_Base_L_Eye", "CC_Base_R_Eye", "CC_Base_L_Eye"]
ROOT_BONE_NAMES = HEAD_BONE_NAMES.copy().extend(JAW_BONE_NAMES.copy())

AVAILABLE_SPRING_RIG_LIST = []


def get_all_parent_modes(chr_cache, arm):
    return ["HEAD", "JAW"]


def get_spring_rig_name(arm, parent_mode):
    if parent_mode == "JAW":
        spring_rig_name = JAW_RIG_NAME
    else:
        spring_rig_name = HEAD_RIG_NAME

    # fix any old spring bone rig names
    old_spring_rig_name = "RL_" + spring_rig_name[4:]
    if old_spring_rig_name in arm.data.bones:
        return old_spring_rig_name

    return spring_rig_name


def has_spring_rig(chr_cache, arm, parent_mode):
    spring_rig_name = get_spring_rig_name(arm, parent_mode)
    spring_rig = bones.get_bone(arm, spring_rig_name)
    return spring_rig is not None


def has_spring_rigs(chr_cache, arm):
    parent_modes = get_all_parent_modes(chr_cache, arm)
    for parent_mode in parent_modes:
        if has_spring_rig(chr_cache, arm, parent_mode):
            return True
    return False


def has_spring_systems(chr_cache):
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            parent_modes = get_all_parent_modes(chr_cache, arm)
            for parent_mode in parent_modes:
                rig_prefix = get_spring_rig_prefix(parent_mode)
                rigid_body_system = rigidbody.get_spring_rigid_body_system(arm, rig_prefix)
                if rigid_body_system:
                    return True
    return False


def get_spring_systems(chr_cache):
    spring_systems = []
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            parent_modes = get_all_parent_modes(chr_cache, arm)
            for parent_mode in parent_modes:
                rig_prefix = get_spring_rig_prefix(parent_mode)
                rigid_body_system = rigidbody.get_spring_rigid_body_system(arm, rig_prefix)
                if rigid_body_system:
                    spring_systems.append(rigid_body_system)
    return spring_systems


def rigidbody_state():
    has_rigidbody = False
    is_baked = False
    is_baking = False
    point_cache = None
    rigidbody_world = bpy.context.scene.rigidbody_world
    if rigidbody_world:
        has_rigidbody = True
        point_cache = rigidbody_world.point_cache
        is_baked = point_cache.is_baked
        is_baking = point_cache.is_baking
    return has_rigidbody, is_baked, is_baking, point_cache


def get_spring_rigs(chr_cache, arm, parent_modes : list = None, mode = "POSE"):
    """Returns { parent_mode: {
                    "name": rig_name,
                    "bone_name": rig_root.name,
                    "bone": rig_root
               } }
       The bone will be either the edit bone, pose bone or bone depending on which mode Blender is in.
       (or the pose if preferred)
       """
    if not parent_modes:
        parent_modes = get_all_parent_modes(chr_cache, arm)
    spring_rigs = {}
    for parent_mode in parent_modes:
        spring_rig_name = get_spring_rig_name(arm, parent_mode)
        spring_rig_bone = get_spring_rig(chr_cache, arm, parent_mode, mode)
        if spring_rig_bone:
            spring_rigs[parent_mode] = { "name": spring_rig_name,
                                         "bone_name" : spring_rig_bone.name,
                                         "bone": spring_rig_bone }
    return spring_rigs


def get_spring_rig_names(chr_cache, arm, parent_modes = None, mode = "POSE"):
    spring_rigs = get_spring_rigs(chr_cache, arm, parent_modes, mode)
    return [v["bone_name"] for v in spring_rigs.values()]


def get_spring_rig_from_child(chr_cache, arm, bone_name, prefer_pose = True):

    try:
        if prefer_pose or utils.get_mode() == "POSE":
            bone = arm.pose.bones[bone_name]
        elif utils.get_mode() == "EDIT":
            bone = arm.data.edit_bones[bone_name]
        else:
            bone = arm.data.bones[bone_name]
    except:
        bone = None

    if bone:

        spring_rigs = get_spring_rigs(chr_cache, arm, mode = "POSE")

        while bone.parent:
            for parent_mode in spring_rigs:
                if spring_rigs[parent_mode]["bone"] == bone.parent:
                    return spring_rigs[parent_mode], bone.name, parent_mode
            bone = bone.parent

    return None, None, None


def get_spring_rig(chr_cache, arm, parent_mode, mode = "POSE", create_if_missing = False):
    """This will return either the edit bone, pose bone or bone depending on which mode Blender is in.
       (or the pose if preferred)
       """
    if parent_mode and chr_cache and arm:
        spring_rig_name = get_spring_rig_name(arm, parent_mode)
        spring_rig = None
        if mode == "EDIT" and utils.get_mode() != "EDIT":
            utils.edit_mode_to(arm)
        if mode == "POSE" or utils.get_mode() == "POSE":
            if spring_rig_name in arm.pose.bones:
                return arm.pose.bones[spring_rig_name]
        elif mode == "EDIT" and utils.get_mode() == "EDIT":
            if spring_rig_name in arm.data.edit_bones:
                spring_rig = arm.data.edit_bones[spring_rig_name]
            if not spring_rig and create_if_missing:
                anchor_bone_name = get_spring_anchor_name(chr_cache, arm, parent_mode)
                center_position = get_spring_rig_position(chr_cache, arm, parent_mode)
                spring_rig = bones.new_edit_bone(arm, spring_rig_name, anchor_bone_name)
                spring_rig.head = arm.matrix_world.inverted() @ center_position
                spring_rig.tail = arm.matrix_world.inverted() @ (center_position + Vector((0,1/32,0)))
                spring_rig.align_roll(Vector((0,0,1)))
                bones.set_bone_collection(arm, spring_rig, "Spring (Root)", None, vars.SPRING_ROOT_LAYER)
                bones.set_bone_collection_visibility(arm, "Spring (Root)", vars.SPRING_ROOT_LAYER, False)
                # TODO spring roots are put in the DEF bones by Rigify...
            return spring_rig
        else:
            if spring_rig_name in arm.data.bones:
                return arm.data.bones[spring_rig_name]
    return None


def get_spring_rig_prefix(parent_mode):
    if parent_mode == "HEAD":
        return HAIR_BONE_PREFIX
    elif parent_mode == "JAW":
        return BEARD_BONE_PREFIX
    else:
        return "NONE"


def get_spring_anchor_name(chr_cache, arm, parent_mode):
    if parent_mode == "HEAD":
        possible_head_bones = HEAD_BONE_NAMES
        for name in possible_head_bones:
            if name in arm.data.bones:
                return name
        return None
    elif parent_mode == "JAW":
        possible_jaw_bones = JAW_BONE_NAMES
        for name in possible_jaw_bones:
            if name in arm.data.bones:
                return name
        return None


def get_spring_rig_position(chr_cache, arm, root_mode):
    """Returns the approximate position inside the head between the ears at nose height."""

    head_edit_bone = get_spring_anchor_edit_bone(chr_cache, arm, "HEAD")

    if head_edit_bone:
        head_pos = arm.matrix_world @ head_edit_bone.head

        eye_pos = Vector((0,0,0))
        count = 0
        for eye_bone_name in EYE_BONE_NAMES:
            eye_edit_bone = bones.get_edit_bone(arm, eye_bone_name)
            if eye_edit_bone:
                count += 1
                eye_pos += arm.matrix_world @ eye_edit_bone.head

        if count > 0:
            eye_pos /= count

            if root_mode == "HEAD":
                return Vector((head_pos[0], head_pos[1], eye_pos[2]))
            elif root_mode == "JAW":
                return Vector((head_pos[0], (head_pos[1] + 2 * eye_pos[1]) / 3, head_pos[2]))
        else:
            return head_pos

    return None


def get_spring_anchor_edit_bone(chr_cache, arm, parent_mode):
    try:
        return arm.data.edit_bones[get_spring_anchor_name(chr_cache, arm, parent_mode)]
    except:
        return None


def is_hair_bone(bone_name):
    if bone_name.startswith(HAIR_BONE_PREFIX) or bone_name.startswith(BEARD_BONE_PREFIX):
        return True
    else:
        return False


def is_hair_rig_bone(bone_name):
    if bone_name.startswith(HEAD_RIG_NAME) or bone_name.startswith(JAW_RIG_NAME):
        return True
    else:
        return False


def convert_spring_rig_to_accessory(chr_cache, arm, parent_mode):
    """Removes all none hair rig vertex groups from objects so that CC4 recognizes them as accessories
       and not cloth or hair.\n\n
       Accessories are categorized by:\n
            1. A bone representing the accessory parented to a CC Base bone. (This is the spring rig root bone)
            2. Child accessory deformation bone(s) parented to the accessory bone in 1.
            3. Object(s) with vertex weights to ONLY these accessory deformation bones in 2.
            4. All vertices in the accessory must be weighted.
    """
    groups_to_remove = []

    # get a list of all bones in the spring rig
    spring_rig_bone = get_spring_rig(chr_cache, arm, parent_mode)
    spring_bones = bones.get_bone_children(spring_rig_bone)
    spring_bone_names = [ bone.name for bone in spring_bones ]

    # find all character objects with vertex groups for these bones
    accessory_objects = set()
    objects = chr_cache.get_all_objects(include_armature=False,
                                        include_children=True,
                                        of_type="MESH")
    for obj in objects:
        for vg in obj.vertex_groups:
            if vg.name in spring_bone_names:
                accessory_objects.add(obj)

    # in these objects remove all vertex groups not from these bones
    for obj in accessory_objects:
        groups_to_remove = []
        for vg in obj.vertex_groups:
            if vg.name not in spring_bone_names:
                groups_to_remove.append(vg)
        for vg in groups_to_remove:
            obj.vertex_groups.remove(vg)


def is_rigified(chr_cache, rig, parent_mode):
    if chr_cache and rig and parent_mode:
        spring_rig = get_spring_rig(chr_cache, rig, parent_mode)
        if spring_rig:
            pose_bone = rig.pose.bones[spring_rig.name]
            if "rigified" in pose_bone and pose_bone["rigified"]:
                return True
            else:
                return False
    return None


def realign_spring_bones_axis(chr_cache, arm):

    utils.edit_mode_to(arm, True)

    # align z-axis away from the spring roots
    spring_rigs = get_spring_rigs(chr_cache, arm, mode = "EDIT")
    for parent_mode in spring_rigs:
        spring_root = spring_rigs[parent_mode]["bone"]
        spring_bones = bones.get_bone_children(spring_root, include_root=False)
        for bone in spring_bones:
            head = arm.matrix_world @ bone.head
            tail = arm.matrix_world @ bone.tail
            origin = arm.matrix_world @ spring_root.head
            z_axis = (((head + tail) * 0.5) - origin).normalized()
            bone.align_roll(z_axis)
            if bone.parent != spring_root:
                bone.use_connect = True

    # save edit mode changes
    utils.object_mode_to(arm)


def enumerate_spring_rigs(self, context):
    global AVAILABLE_SPRING_RIG_LIST
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)

    if chr_cache:
        arm = chr_cache.get_armature()

        spring_rigs = get_spring_rigs(chr_cache, arm, mode = "POSE")
        AVAILABLE_SPRING_RIG_LIST.clear()
        for i, parent_mode in enumerate(spring_rigs):
            list_entry = (parent_mode, f"{parent_mode} Rig", f"{parent_mode} Rig")
            AVAILABLE_SPRING_RIG_LIST.append(list_entry)

        if not spring_rigs:
            AVAILABLE_SPRING_RIG_LIST.append(("NONE", "No Rig", "No Rig"))

    return AVAILABLE_SPRING_RIG_LIST


def show_spring_bone_edit_layer(chr_cache, arm, show):
    if arm:
        if show:
            bones.set_bone_collection_visibility(arm, "Spring (Edit)", vars.SPRING_EDIT_LAYER, True, only=True)
            arm.show_in_front = True
            arm.display_type = 'SOLID'
            #arm.data.display_type = 'STICK'

        else:
            bones.set_bone_collection_visibility(arm, "Spring (Edit)", vars.SPRING_EDIT_LAYER, False, only=True)
            arm.show_in_front = False
            if chr_cache.rigified:
                arm.display_type = 'WIRE'
            else:
                arm.display_type = 'SOLID'
            #arm.data.display_type = 'OCTAHEDRAL'


def show_spring_bone_rig_layers(chr_cache, arm, show):
    if arm:
        if show:
            bones.set_bone_collection_visibility(arm, "Spring (FK)", vars.SPRING_FK_LAYER, True)
            arm.show_in_front = False

        else:
            bones.set_bone_collection_visibility(arm, "Spring (FK)", vars.SPRING_FK_LAYER, False)
            arm.show_in_front = False
            if chr_cache.rigified:
                arm.display_type = 'WIRE'
            else:
                arm.display_type = 'SOLID'
            #arm.data.display_type = 'OCTAHEDRAL'


def stop_spring_animation(context):
    # stop any playing animation
    if context.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)

    # reset the animation (it is very unstable if we don't do this)
    bpy.ops.screen.frame_jump(end = False)


def reset_spring_physics(context):
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            arm.data.pose_position = "POSE"

    # reset the physics cache
    bpy.context.scene.frame_current = bpy.context.scene.frame_current + 1
    rigidbody.reset_cache(context)

    # reset the animation again for good measure...
    bpy.ops.screen.frame_jump(end = True)
    bpy.ops.screen.frame_jump(end = False)


def add_spring_colliders(chr_cache):
    arm = chr_cache.get_armature()
    if not rigidbody.has_rigid_body_colliders(arm):
        json_data = chr_cache.get_json_data()
        bone_mapping = None
        if chr_cache.rigified:
            bone_mapping = chr_cache.get_rig_bone_mapping()
        rigidbody.build_rigid_body_colliders(chr_cache, json_data, bone_mapping=bone_mapping)


def toggle_show_spring_bones(chr_cache):
    if chr_cache:
        arm = chr_cache.get_armature()
    else:
        arm = utils.get_armature_from_objects(bpy.context.selected_objects)
    if arm:
        if bones.is_bone_collection_visible(arm, "Spring (Edit)", vars.SPRING_EDIT_LAYER):
            show_spring_bone_edit_layer(chr_cache, arm, False)
        else:
            show_spring_bone_edit_layer(chr_cache, arm, True)


class CC3OperatorSpringBones(bpy.types.Operator):
    """Blender Spring Bone Functions"""
    bl_idname = "cc3.springbones"
    bl_label = "Spring Bone Simulation"
    #bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        mode_selection = utils.store_mode_selection_state()

        chr_cache = props.get_context_character_cache(context)
        arm = None
        if chr_cache:
            arm = chr_cache.get_armature()

        if self.param == "MAKE_RIGID_BODY_SYSTEM":
            stop_spring_animation(context)

            if arm:
                parent_mode = chr_cache.available_spring_rigs
                spring_rig_name = get_spring_rig_name(arm, parent_mode)
                spring_rig_prefix = get_spring_rig_prefix(parent_mode)

                rigidbody.build_spring_rigid_body_system(chr_cache, spring_rig_prefix, spring_rig_name)
                add_spring_colliders(chr_cache)

            reset_spring_physics(context)

            utils.restore_mode_selection_state(mode_selection)

        if self.param == "REMOVE_RIGID_BODY_SYSTEM":
            stop_spring_animation(context)

            if arm:
                parent_mode = props.hair_rig_bone_root
                spring_rig_name = get_spring_rig_name(arm, parent_mode)
                spring_rig_prefix = get_spring_rig_prefix(parent_mode)

                rigidbody.remove_existing_rigid_body_system(arm, spring_rig_prefix, spring_rig_name)

            reset_spring_physics(context)

        if self.param == "ENABLE_RIGID_BODY_COLLISION":
            stop_spring_animation(context)

            objects = utils.get_selected_meshes(context)
            for body in objects:
                rigidbody.enable_rigid_body_collision_mesh(chr_cache, body)

            reset_spring_physics(context)

            utils.restore_mode_selection_state(mode_selection)

        if self.param == "DISABLE_RIGID_BODY_COLLISION":
            stop_spring_animation(context)

            objects = utils.get_selected_meshes(context)
            for obj in objects:
                rigidbody.disable_rigid_body_collision_mesh(chr_cache, obj)

            reset_spring_physics(context)

            utils.restore_mode_selection_state(mode_selection)

        if self.param == "RESET_PHYSICS":
            stop_spring_animation(context)
            reset_spring_physics(context)

            utils.restore_mode_selection_state(mode_selection)

        elif self.param == "BUILD_COLLIDERS":
            stop_spring_animation(context)
            reset_spring_physics(context)
            add_spring_colliders(chr_cache)
            rigidbody.toggle_show_colliders(arm)
            utils.restore_mode_selection_state(mode_selection)

        elif self.param == "REMOVE_COLLIDERS":
            stop_spring_animation(context)
            reset_spring_physics(context)
            rigidbody.remove_rigid_body_colliders(arm)
            #utils.restore_mode_selection_state(mode_selection)

        elif self.param == "TOGGLE_SHOW_COLLIDERS":
            rigidbody.toggle_show_colliders(arm)
            #utils.restore_mode_selection_state(mode_selection)

        if self.param == "BAKE_PHYSICS":
            utils.object_mode_to(arm)
            reset_spring_physics(context)
            utils.log_info("Baking rigid body world point cache...")
            bpy.ops.ptcache.bake({"point_cache": bpy.context.scene.rigidbody_world.point_cache},
                                 "INVOKE_DEFAULT", bake=True)
            # as py.ops.ptcache.bake is a modal operator, don't do *anything* afterwards,
            # or Blender will crash...
            return {"FINISHED"}

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        props = vars.props()

        if properties.param == "MAKE_RIGID_BODY_SYSTEM":
            return "Build the rigid body simulation for the selected spring rig and sets contraints to copy the simulation to the spring bones"
        elif properties.param == "REMOVE_RIGID_BODY_SYSTEM":
            return "Removes the rigid body simulation for the selected spring rig and removes all constraints"
        elif properties.param == "ENABLE_RIGID_BODY_COLLISION":
            return "Enables rigid body collision for the selected mesh (or it's collision proxy mesh), so it can interact with the spring bone simulation"
        elif properties.param == "DISABLE_RIGID_BODY_COLLISION":
            return "Removes rigid body collision for the selected mesh (or it's collision proxy mesh), so it can interact with the spring bone simulation"
        elif properties.param == "RESET_PHYSICS":
            return "Resets the spring bone physics rigid body world point cache and synchronizes the cache range with the current scene or preview range"
        elif properties.param == "BAKE_PHYSICS":
            return "Bakes the rigid body world point cache for all spring bone simulations"
        return ""
