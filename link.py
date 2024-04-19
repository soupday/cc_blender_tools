import bpy, bpy_extras
import bpy_extras.view3d_utils as v3d
import atexit
from enum import IntEnum
import os, socket, time, select, struct, json
import subprocess
from mathutils import Vector, Quaternion, Matrix
from . import importer, bones, geom, colorspace, rigging, rigutils, utils, vars


BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 300
PING_INTERVAL_S = 120
TIMER_INTERVAL = 1/30
MAX_CHUNK_SIZE = 32768
SERVER_ONLY = False
CLIENT_ONLY = True
CHARACTER_TEMPLATE: list = None
MAX_RECEIVE = 30
USE_PING = False
USE_KEEPALIVE = False
SOCKET_TIMEOUT = 5.0

class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    NOTIFY = 50
    SAVE = 60
    MORPH = 90
    MORPH_UPDATE = 91
    CHARACTER = 100
    CHARACTER_UPDATE = 101
    PROP = 102
    PROP_UPDATE = 103
    RIGIFY = 110
    TEMPLATE = 200
    POSE = 210
    POSE_FRAME = 211
    SEQUENCE = 220
    SEQUENCE_FRAME = 221
    SEQUENCE_END = 222
    SEQUENCE_ACK = 223
    LIGHTS = 230
    CAMERA_SYNC = 231
    FRAME_SYNC = 232


VISEME_NAME_MAP = {
    "None": "None",
    "Open": "V_Open",
    "Explosive": "V_Explosive",
    "Upper Dental": "V_Dental_Lip",
    "Tight O": "V_Tight_O",
    "Pucker": "V_Tight",
    "Wide": "V_Wide",
    "Affricate": "V_Affricate",
    "Lips Parted": "V_Lip_Open",
    "Tongue Up": "V_Tongue_up",
    "Tongue Raised": "V_Tongue_Raise",
    "Tongue Out": "V_Tongue_Out",
    "Tongue Narrow": "V_Tongue_Narrow",
    "Tongue Lower": "V_Tongue_Lower",
    "Tongue Curl-U": "V_Tongue_Curl_U",
    "Tongue Curl-D": "V_Tongue_Curl_D",
    "EE": "EE",
    "Er": "Er",
    "Ih": "IH",
    "Ah": "Ah",
    "Oh": "Oh",
    "W.OO": "W_OO",
    "S.Z": "S_Z",
    "Ch.J": "Ch_J",
    "F.V": "F_V",
    "Th": "TH",
    "T.L.D": "T_L_D_N",
    "B.M.P": "B_M_P",
    "K.G": "K_G_H_NG",
    "N.NG": "AE",
    "R": "R",
}


class LinkActor():
    name: str = "Name"
    chr_cache = None
    bones: list = []
    skin_meshes: dict = {}
    meshes: list = []
    rig_bones: list = []
    expressions: list = []
    visemes: list = []
    morphs: list = []
    cache: dict = None
    alias: list = []
    shape_keys: dict = {}

    def __init__(self, chr_cache):
        self.chr_cache = chr_cache
        self.name = chr_cache.character_name
        return

    def get_chr_cache(self):
        return self.chr_cache

    def get_link_id(self):
        chr_cache = self.get_chr_cache()
        if chr_cache:
            return chr_cache.get_link_id()
        return None

    def get_armature(self):
        chr_cache = self.get_chr_cache()
        if chr_cache:
            return chr_cache.get_armature()
        return None

    def select(self):
        chr_cache = self.get_chr_cache()
        if chr_cache:
            chr_cache.select_all()

    def get_type(self):
        chr_cache = self.get_chr_cache()
        return self.chr_cache_type(chr_cache)

    def add_alias(self, link_id):
        chr_cache = self.get_chr_cache()
        if chr_cache:
            actor_link_id = chr_cache.link_id
            if not actor_link_id:
                utils.log_info(f"Assigning actor link_id: {chr_cache.character_name}: {link_id}")
                chr_cache.link_id = link_id
                return
            if link_id not in self.alias and actor_link_id != link_id:
                utils.log_info(f"Assigning actor alias: {chr_cache.character_name}: {link_id}")
                self.alias.append(link_id)
                return

    @staticmethod
    def find_actor(link_id, search_name=None, search_type=None):
        props = bpy.context.scene.CC3ImportProps

        utils.log_detail(f"Looking for LinkActor: {search_name} {link_id} {search_type}")
        actor: LinkActor = None

        chr_cache = props.find_character_by_link_id(link_id)
        if chr_cache:
            if not search_type or LinkActor.chr_cache_type(chr_cache) == search_type:
                actor = LinkActor(chr_cache)
                utils.log_detail(f"Chr found by link_id: {actor.name} / {link_id}")
                return actor
        utils.log_detail(f"Chr not found by link_id")

        # try to find the character by name if the link id finds nothing
        # character id's change after every reload in iClone/CC4 so these can change.
        if search_name:
            chr_cache = props.find_character_by_name(search_name)
            if chr_cache:
                if not search_type or LinkActor.chr_cache_type(chr_cache) == search_type:
                    utils.log_detail(f"Chr found by name: {chr_cache.character_name} / {chr_cache.link_id} -> {link_id}")
                    actor = LinkActor(chr_cache)
                    actor.add_alias(link_id)
                    return actor
            utils.log_detail(f"Chr not found by name")

        # finally if connected to character creator fall back to the first character
        # as character creator only ever has one character in the scene.
        if get_link_data().is_cc() and search_type == "AVATAR":
            chr_cache = props.get_first_avatar()
            if chr_cache:
                utils.log_detail(f"Falling back to first Chr Avatar: {chr_cache.character_name} / {chr_cache.link_id} -> {link_id}")
                actor = LinkActor(chr_cache)
                actor.add_alias(link_id)
                return actor

        utils.log_info(f"LinkActor not found: {search_name} {link_id} {search_type}")
        return actor

    @staticmethod
    def chr_cache_type(chr_cache):
        if chr_cache:
            if chr_cache.is_avatar():
                return "AVATAR"
            else:
                return "PROP"
        return "NONE"

    def get_mesh_objects(self):
        objects = None
        chr_cache = self.get_chr_cache()
        if chr_cache:
            objects = chr_cache.get_all_objects(include_armature=False,
                                                include_children=True,
                                                of_type="MESH")
        return objects

    def object_has_sequence_shape_keys(self, obj):
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            for expression_name in self.expressions:
                if expression_name in obj.data.shape_keys.key_blocks:
                    return True
            for viseme_name in self.visemes:
                if viseme_name in obj.data.shape_keys.key_blocks:
                    return True
        return False

    def collect_shape_keys(self):
        self.shape_keys.clear()
        objects: list = self.get_mesh_objects()
        # sort objects by reverse shape_key count (this should put the body mesh first)
        objects.sort(key=utils.key_count, reverse=True)
        # collect dictionary of shape keys and their primary key block
        for obj in objects:
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                for key in obj.data.shape_keys.key_blocks:
                    if key.name not in self.shape_keys:
                        self.shape_keys[key.name] = key

    def get_sequence_objects(self):
        objects = []
        chr_cache = self.get_chr_cache()
        if chr_cache:
            all_objects = chr_cache.get_all_objects(include_armature=False,
                                                     include_children=True,
                                                     of_type="MESH")
            for obj in all_objects:
                if self.object_has_sequence_shape_keys(obj):
                    objects.append(obj)
        return objects

    def set_template(self, bones, meshes, expressions, visemes, morphs):
        self.bones = bones
        self.meshes = meshes
        self.expressions = expressions
        self.visemes = self.remap_visemes(visemes)
        self.morphs = morphs
        rig = self.get_armature()
        skin_meshes = {}
        for mesh_name in meshes:
            obj = None
            for child in rig.children:
                if child.type == "MESH" and child.name == mesh_name:
                    obj = child
                    obj.rotation_mode = "QUATERNION"
                    skin_meshes[mesh_name] = [obj, obj.location.copy(), obj.rotation_quaternion.copy(), obj.scale.copy()]
        self.skin_meshes = skin_meshes

    def remap_visemes(self, visemes):
        exported_visemes = []
        for viseme_name in visemes:
            if viseme_name in VISEME_NAME_MAP:
                exported_visemes.append(VISEME_NAME_MAP[viseme_name])
        return exported_visemes

    def clear_template(self):
        self.bones = None

    def set_cache(self, cache):
        self.cache = cache

    def clear_cache(self):
        self.cache = None

    def update_name(self, new_name):
        self.name = new_name
        chr_cache = self.get_chr_cache()
        if chr_cache:
            chr_cache.character_name = new_name

    def update_link_id(self, new_link_id):
        chr_cache = self.get_chr_cache()
        if chr_cache:
            utils.log_info(f"Assigning new link_id: {chr_cache.character_name}: {new_link_id}")
            chr_cache.link_id = new_link_id

    def ready(self):
        if self.cache and self.get_chr_cache() and self.get_armature():
            return True
        else:
            return False


class LinkData():
    link_host: str = "localhost"
    link_host_ip: str = "127.0.0.1"
    link_target: str = "BLENDER"
    link_port: int = 9333
    actors: list = []
    # Sequence/Pose Props
    sequence_current_frame: int = 0
    sequence_start_frame: int = 0
    sequence_end_frame: int = 0
    sequence_actors: list = None
    #
    preview_shape_keys: bool = True
    preview_skip_frames: bool = False
    # remote props
    remote_app: str = None
    remote_version: str = None
    remote_path: str = None
    remote_exe: str = None
    #
    ack_rate: float = 0.0
    ack_time: float = 0.0

    def __init__(self):
        return

    def reset(self):
        self.actors = []
        self.sequence_actors = None
        self.sequence_actors = None

    def is_cc(self):
        if self.remote_app == "Character Creator":
            return True
        else:
            return False

    def find_sequence_actor(self, link_id) -> LinkActor:
        for actor in self.sequence_actors:
            if actor.get_link_id() == link_id:
                return actor
        for actor in self.sequence_actors:
            if link_id in actor.alias:
                return actor
        return None


LINK_DATA = LinkData()

def get_link_data():
    global LINK_DATA
    return LINK_DATA


def encode_from_json(json_data) -> bytearray:
    json_string = json.dumps(json_data)
    json_bytes = bytearray(json_string, "utf-8")
    return json_bytes


def decode_to_json(data) -> dict:
    text = data.decode("utf-8")
    json_data = json.loads(text)
    return json_data


def pack_string(s) -> bytearray:
    buffer = bytearray()
    buffer += struct.pack("!I", len(s))
    buffer += bytes(s, encoding="utf-8")
    return buffer


def unpack_string(buffer, offset=0):
    length = struct.unpack_from("!I", buffer, offset)[0]
    offset += 4
    string: bytearray = buffer[offset:offset+length]
    offset += length
    return offset, string.decode(encoding="utf-8")


def get_local_data_path():
    local_path = utils.local_path()
    blend_file_name = utils.blend_file_name()
    data_path = ""
    if local_path and blend_file_name:
        data_path = local_path
    return data_path


def find_rig_pivot_bone(rig, parent):
    bone: bpy.types.PoseBone
    for bone in rig.pose.bones:
        if bone.name.startswith("CC_Base_Pivot"):
            if bones.is_target_bone_name(bone.parent.name, parent):
                return bone.name
    return None



def make_datalink_import_rig(actor: LinkActor):
    """Creates or re-uses and existing datalink pose rig for the character.
       This uses a pre-generated character template (list of bones in the character)
       sent from CC/iC to avoid encoding the bone names into the pose data stream."""

    if not actor:
        utils.log_error("make_datalink_import_rig - Invalid Actor:")
        return None
    if not actor.get_chr_cache():
        utils.log_error(f"make_datalink_import_rig - Invalid Actor cache: {actor.name}")
        return None
    # get character armature
    chr_rig = actor.get_armature()
    if not chr_rig:
        utils.log_error(f"make_datalink_import_rig - Invalid Actor armature: {actor.name}")
        return None
    chr_rig.hide_set(False)
    chr_cache = actor.get_chr_cache()
    is_prop = actor.get_type() == "PROP"

    if utils.object_exists_is_armature(chr_cache.rig_datalink_rig):
        chr_cache.rig_datalink_rig.hide_set(False)
        #utils.log_info(f"Using existing datalink transfer rig: {chr_cache.rig_datalink_rig.name}")
        return chr_cache.rig_datalink_rig

    no_constraints = True if chr_cache.rigified else False

    rig_name = f"{chr_cache.character_name}_Link_Rig"
    utils.log_info(f"Creating datalink transfer rig: {rig_name}")

    # create pose armature
    datalink_rig = utils.get_armature(rig_name)
    if not datalink_rig:
        datalink_rig = utils.create_reuse_armature(rig_name)
        edit_bone: bpy.types.EditBone
        arm: bpy.types.Armature = datalink_rig.data
        if utils.edit_mode_to(datalink_rig):
            while len(datalink_rig.data.edit_bones) > 0:
                datalink_rig.data.edit_bones.remove(datalink_rig.data.edit_bones[0])
            actor.rig_bones = actor.bones.copy()
            for i, sk_bone_name in enumerate(actor.bones):
                edit_bone = arm.edit_bones.new(sk_bone_name)
                actor.rig_bones[i] = edit_bone.name
                edit_bone.head = Vector((0,0,0))
                edit_bone.tail = Vector((0,1,0))
                edit_bone.align_roll(Vector((0,0,1)))
                edit_bone.length = 0.1

        utils.object_mode_to(datalink_rig)

        # constraint character armature
        l = len(actor.bones)
        if not no_constraints:
            for i, rig_bone_name in enumerate(actor.rig_bones):
                sk_bone_name = actor.bones[i]
                # for now, ignore all pivot bones
                if sk_bone_name == "_Object_Pivot_Node_":
                    continue
                chr_bone_name = bones.find_target_bone_name(chr_rig, rig_bone_name)
                if chr_bone_name:
                    bones.add_copy_location_constraint(datalink_rig, chr_rig, rig_bone_name, chr_bone_name)
                    bones.add_copy_rotation_constraint(datalink_rig, chr_rig, rig_bone_name, chr_bone_name)
                else:
                    utils.log_warn(f"Could not find bone: {rig_bone_name} in character rig!")
        utils.safe_set_action(datalink_rig, None)

    utils.object_mode_to(datalink_rig)
    datalink_rig.hide_set(True)

    chr_cache.rig_datalink_rig = datalink_rig

    if chr_cache.rigified:
        # a rigified character must retarget the link rig, but...
        # the link rig doesn't have a valid bind pose, so the retargeting rig
        # can't use it as a source rig for the roll axes on the ORG bones,
        # so we use the original ones for the character type (option to_original_rig)
        # (data on the original bones is added the ORG bones during rigify process)
        rigging.adv_retarget_remove_pair(None, chr_cache)
        if not chr_cache.rig_retarget_rig:
            rigging.adv_retarget_pair_rigs(None, chr_cache,
                                        source_rig_override=datalink_rig,
                                        to_original_rig=True)

    return datalink_rig


def remove_datalink_import_rig(actor: LinkActor):
    if actor:
        chr_cache = actor.get_chr_cache()
        chr_rig = actor.get_armature()

        if utils.object_exists_is_armature(chr_cache.rig_datalink_rig):

            if chr_cache.rigified:
                rigging.adv_retarget_remove_pair(None, chr_cache)

            else:
                # remove all contraints on the character rig
                if utils.object_exists(chr_rig):
                    chr_rig.hide_set(False)
                    if utils.object_mode_to(chr_rig):
                        for pose_bone in chr_rig.pose.bones:
                            bones.clear_constraints(chr_rig, pose_bone.name)

            utils.delete_armature_object(chr_cache.rig_datalink_rig)
            chr_cache.rig_datalink_rig = None

        #rigging.reset_shape_keys(chr_cache)
        utils.object_mode_to(chr_rig)


def set_actor_expression_weight(objects, expression_name, weight):
    global LINK_DATA
    if objects and LINK_DATA.preview_shape_keys:
        obj: bpy.types.Object
        for obj in objects:
            if expression_name in obj.data.shape_keys.key_blocks:
                if obj.data.shape_keys.key_blocks[expression_name].value != weight:
                    obj.data.shape_keys.key_blocks[expression_name].value = weight


def set_actor_viseme_weight(objects, viseme_name, weight):
    global LINK_DATA
    if objects and LINK_DATA.preview_shape_keys:
        for obj in objects:
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                if viseme_name in obj.data.shape_keys.key_blocks:
                    if obj.data.shape_keys.key_blocks[viseme_name].value != weight:
                        obj.data.shape_keys.key_blocks[viseme_name].value = weight


def ensure_current_frame(current_frame):
    if bpy.context.scene.frame_current != current_frame:
        bpy.context.scene.frame_current = current_frame
    return current_frame


def next_frame(current_frame=None):
    if current_frame is None:
        current_frame = bpy.context.scene.frame_current
    fps = bpy.context.scene.render.fps
    end_frame = bpy.context.scene.frame_end
    current_frame = min(end_frame, current_frame + 1)
    bpy.context.scene.frame_current = current_frame
    return current_frame


def reset_action(chr_cache):
    if chr_cache:
        rig = chr_cache.get_armature()
        if rig:
            action = utils.safe_get_action(rig)
            action.fcurves.clear()


def create_fcurves_cache(count, indices, defaults):
    curves = []
    cache = {
        "count": count,
        "indices": indices,
        "curves": curves,
    }
    for i in range(0, indices):
        d = defaults[i]
        cache_data = [d]*(count*2)
        curves.append(cache_data)
    return cache


def prep_rig(actor: LinkActor, start_frame, end_frame):
    """Prepares the character rig for keyframing poses from the pose data stream."""

    if actor and actor.get_chr_cache():
        chr_cache = actor.get_chr_cache()
        rig = actor.get_armature()
        if not rig:
            utils.log_error(f"Actor: {actor.name} invalid rig!")
            return
        objects = actor.get_sequence_objects()
        if rig:
            rig_name = utils.strip_name(rig.name)
            utils.log_info(f"Preparing Character Rig: {actor.name} {rig_name} / {len(actor.bones)} bones")


            # rig action
            action_name = f"{rig_name}|A|Datalink"
            utils.log_info(f"Preparing rig action: {action_name}")
            if action_name in bpy.data.actions:
                action = bpy.data.actions[action_name]
            else:
                action = bpy.data.actions.new(action_name)
            action.fcurves.clear()
            utils.safe_set_action(rig, action)

            # shape key actions
            num_expressions = len(actor.expressions)
            num_visemes = len(actor.visemes)
            if objects:
                for obj in objects:
                    obj_name = utils.strip_name(obj.name)
                    action_name = f"{rig_name}|K|{obj_name}|Datalink"
                    utils.log_info(f"Preparing shape key action: {action_name} / {num_expressions}+{num_visemes} shape keys")
                    if action_name in bpy.data.actions:
                        action = bpy.data.actions[action_name]
                    else:
                        action = bpy.data.actions.new(action_name)
                    action.fcurves.clear()
                    utils.safe_set_action(obj.data.shape_keys, action)

            if chr_cache.rigified:
                BAKE_BONE_GROUPS = ["FK", "IK", "Special", "Root"] #not Tweak and Extra
                BAKE_BONE_COLLECTIONS = ["Face", "Face (Primary)", "Face (Secondary)",
                                         "Torso", "Torso (Tweak)",
                                         "Fingers", "Fingers (Detail)",
                                         "Arm.L (IK)", "Arm.L (FK)", "Arm.L (Tweak)",
                                         "Leg.L (IK)", "Leg.L (FK)", "Leg.L (Tweak)",
                                         "Arm.R (IK)", "Arm.R (FK)", "Arm.R (Tweak)",
                                         "Leg.R (IK)", "Leg.R (FK)", "Leg.R (Tweak)",
                                         "Root"]
                BAKE_BONE_LAYERS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,28]
                if utils.object_mode_to(rig):
                    bone: bpy.types.Bone
                    pose_bone: bpy.types.PoseBone
                    bones.make_bones_visible(rig, collections=BAKE_BONE_COLLECTIONS, layers=BAKE_BONE_LAYERS)
                    for pose_bone in rig.pose.bones:
                        bone = pose_bone.bone
                        bone.select = False
                        if bones.is_bone_in_collections(rig, bone, BAKE_BONE_COLLECTIONS,
                                                                BAKE_BONE_GROUPS):
                            bone.hide = False
                            bone.hide_select = False
                            bone.select = True
                            pose_bone.rotation_mode = "QUATERNION"
            else:
                if utils.object_mode_to(rig):
                    bone: bpy.types.Bone
                    pose_bone: bpy.types.PoseBone
                    for pose_bone in rig.pose.bones:
                        bone = pose_bone.bone
                        bone.hide = False
                        bone.hide_select = False
                        bone.select = True
                        pose_bone.rotation_mode = "QUATERNION"

            # create keyframe cache for animation sequences
            count = end_frame - start_frame + 1
            bone_cache = {}
            expression_cache = {}
            viseme_cache = {}
            morph_cache = {}
            actor_cache = {
                "rig": rig,
                "bones": bone_cache,
                "expressions": expression_cache,
                "visemes": viseme_cache,
                "morphs": morph_cache,
                "start": start_frame,
                "end": end_frame,
            }
            for pose_bone in rig.pose.bones:
                bone_name = pose_bone.name
                bone = rig.data.bones[bone_name]
                if bone.select:
                    loc_cache = create_fcurves_cache(count, 3, [0,0,0])
                    sca_cache = create_fcurves_cache(count, 3, [1,1,1])
                    rot_cache = create_fcurves_cache(count, 4, [1,0,0,0])
                    bone_cache[bone_name] = {
                        "loc": loc_cache,
                        "sca": sca_cache,
                        "rot": rot_cache,
                    }

            for expression_name in actor.expressions:
                expression_cache[expression_name] = create_fcurves_cache(count, 1, [0])

            for viseme_name in actor.visemes:
                viseme_cache[viseme_name] = create_fcurves_cache(count, 1, [0])

            for morph_name in actor.morphs:
                pass

            actor.set_cache(actor_cache)


def set_frame_range(start, end):
    bpy.data.scenes["Scene"].frame_start = start
    bpy.data.scenes["Scene"].frame_end = end


def set_frame(frame):
    bpy.data.scenes["Scene"].frame_current = frame
    bpy.context.view_layer.update()


def key_frame_pose_visual():
    area = [a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    with bpy.context.temp_override(area=area):
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_VisualLocRot')


def store_bone_cache_keyframes(actor: LinkActor, frame):
    """Needs to be called after all constraints have been set and all bones in the pose positioned"""

    if not actor.cache:
        utils.log_error(f"No actor cache: {actor.name}")
        return

    rig = actor.get_armature()
    start_frame = actor.cache["start"]
    cache_index = (frame - start_frame) * 2
    bone_cache = actor.cache["bones"]
    for bone_name in bone_cache:
        loc_cache = bone_cache[bone_name]["loc"]
        sca_cache = bone_cache[bone_name]["sca"]
        rot_cache = bone_cache[bone_name]["rot"]
        pose_bone: bpy.types.PoseBone = rig.pose.bones[bone_name]
        L: Matrix   # local space matrix we want
        NL: Matrix  # non-local space matrix we want (if not using local location or inherit rotation)
        M: Matrix = pose_bone.matrix # object space matrix of the pose bone after contraints and drivers
        R: Matrix = pose_bone.bone.matrix_local # bone rest pose matrix
        RI: Matrix = R.inverted() # bone rest pose matrix inverted
        if pose_bone.parent:
            PI: Matrix = pose_bone.parent.matrix.inverted() # parent object space matrix inverted (after contraints and drivers)
            PR: Matrix = pose_bone.parent.bone.matrix_local # parent rest pose matrix
            L = RI @ (PR @ (PI @ M))
            NL = PI @ M
        else:
            L = RI @ M
            NL = M
        if not pose_bone.bone.use_local_location:
            loc = NL.to_translation()
        else:
            loc = L.to_translation()
        sca = L.to_scale()
        if not pose_bone.bone.use_inherit_rotation:
            rot = NL.to_quaternion()
        else:
            rot = L.to_quaternion()
        for i in range(0, 3):
            curve = loc_cache["curves"][i]
            curve[cache_index] = frame
            curve[cache_index + 1] = loc[i]
        for i in range(0, 3):
            curve = sca_cache["curves"][i]
            curve[cache_index] = frame
            curve[cache_index + 1] = sca[i]
        for i in range(0, 4):
            curve = rot_cache["curves"][i]
            curve[cache_index] = frame
            curve[cache_index + 1] = rot[i]


def store_shape_key_cache_keyframes(actor: LinkActor, frame, expression_weights, viseme_weights, morph_weights):
    if not actor.cache:
        utils.log_error(f"No actor cache: {actor.name}")
        return

    start_frame = actor.cache["start"]
    cache_index = (frame - start_frame) * 2

    expression_cache = actor.cache["expressions"]
    for i, expression_name in enumerate(expression_cache):
        curve = expression_cache[expression_name]["curves"][0]
        curve[cache_index] = frame
        curve[cache_index + 1] = expression_weights[i]

    viseme_cache = actor.cache["visemes"]
    for i, viseme_name in enumerate(viseme_cache):
        curve = viseme_cache[viseme_name]["curves"][0]
        curve[cache_index] = frame
        curve[cache_index + 1] = viseme_weights[i]


def write_sequence_actions(actor: LinkActor):
    if actor.cache:
        rig = actor.cache["rig"]
        rig_action = utils.safe_get_action(rig)
        objects = actor.get_sequence_objects()

        if rig_action:
            rig_action.fcurves.clear()
            bone_cache = actor.cache["bones"]
            for bone_name in bone_cache:
                pose_bone: bpy.types.PoseBone = rig.pose.bones[bone_name]
                loc_cache = bone_cache[bone_name]["loc"]
                sca_cache = bone_cache[bone_name]["sca"]
                rot_cache = bone_cache[bone_name]["rot"]
                fcurve: bpy.types.FCurve
                for i in range(0, 3):
                    data_path = pose_bone.path_from_id("location")
                    fcurve = rig_action.fcurves.new(data_path, index=i, action_group="Location")
                    fcurve.keyframe_points.add(loc_cache["count"])
                    fcurve.keyframe_points.foreach_set('co', loc_cache["curves"][i])
                for i in range(0, 3):
                    data_path = pose_bone.path_from_id("scale")
                    fcurve = rig_action.fcurves.new(data_path, index=i, action_group="Scale")
                    fcurve.keyframe_points.add(sca_cache["count"])
                    fcurve.keyframe_points.foreach_set('co', sca_cache["curves"][i])
                for i in range(0, 4):
                    data_path = pose_bone.path_from_id("rotation_quaternion")
                    fcurve = rig_action.fcurves.new(data_path, index=i, action_group="Rotation Quaternion")
                    fcurve.keyframe_points.add(rot_cache["count"])
                    fcurve.keyframe_points.foreach_set('co', rot_cache["curves"][i])

        expression_cache = actor.cache["expressions"]
        viseme_cache = actor.cache["visemes"]
        for obj in objects:
            obj_action = utils.safe_get_action(obj.data.shape_keys)
            if obj_action:
                for expression_name in expression_cache:
                    if expression_name in obj.data.shape_keys.key_blocks:
                        key_cache = expression_cache[expression_name]
                        key = obj.data.shape_keys.key_blocks[expression_name]
                        data_path = key.path_from_id("value")
                        fcurve = obj_action.fcurves.new(data_path, action_group="Expression")
                        fcurve.keyframe_points.add(key_cache["count"])
                        fcurve.keyframe_points.foreach_set('co', key_cache["curves"][0])
                for viseme_name in viseme_cache:
                    if viseme_name in obj.data.shape_keys.key_blocks:
                        key_cache = viseme_cache[viseme_name]
                        key = obj.data.shape_keys.key_blocks[viseme_name]
                        data_path = key.path_from_id("value")
                        fcurve = obj_action.fcurves.new(data_path, action_group="Viseme")
                        fcurve.keyframe_points.add(key_cache["count"])
                        fcurve.keyframe_points.foreach_set('co', key_cache["curves"][0])

        actor.clear_cache()


class Signal():
    callbacks: list = None

    def __init__(self):
        self.callbacks = []

    def connect(self, func):
        self.callbacks.append(func)

    def disconnect(self, func=None):
        if func:
            self.callbacks.remove(func)
        else:
            self.callbacks.clear()

    def emit(self, *args):
        for func in self.callbacks:
            func(*args)


class LinkService():
    timer = None
    server_sock: socket.socket = None
    client_sock: socket.socket = None
    server_sockets = []
    client_sockets = []
    empty_sockets = []
    client_ip: str = "127.0.0.1"
    client_port: int = BLENDER_PORT
    is_listening: bool = False
    is_connected: bool = False
    is_connecting: bool = False
    ping_timer: float = 0
    keepalive_timer: float = 0
    time: float = 0
    is_data: bool = False
    is_sequence: bool = False
    is_import: bool = False
    loop_rate: float = 0.0
    loop_count: int = 0
    sequence_send_count: int = 5
    sequence_send_rate: float = 5.0
    # Signals
    listening = Signal()
    connecting = Signal()
    connected = Signal()
    lost_connection = Signal()
    server_stopped = Signal()
    client_stopped = Signal()
    received = Signal()
    accepted = Signal()
    sent = Signal()
    changed = Signal()
    sequence = Signal()
    # local props
    local_app: str = None
    local_version: str = None
    local_path: str = None
    # remote props
    remote_app: str = None
    remote_version: str = None
    remote_path: str = None
    remote_exe: str = None
    link_data: LinkData = None

    def __init__(self):
        global LINK_DATA
        self.link_data = LINK_DATA
        atexit.register(self.service_stop)

    def __enter__(self):
        return self

    def __exit__(self):
        self.service_stop()

    def is_cc(self):
        return self.remote_app == "Character Creator"

    def is_iclone(self):
        return self.remote_app == "iClone"

    def start_server(self):
        if not self.server_sock:
            try:
                self.keepalive_timer = HANDSHAKE_TIMEOUT_S
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.settimeout(SOCKET_TIMEOUT)
                self.server_sock.bind(('', BLENDER_PORT))
                self.server_sock.listen(5)
                #self.server_sock.setblocking(False)
                self.server_sockets = [self.server_sock]
                self.is_listening = True
                utils.log_info(f"Listening on TCP *:{BLENDER_PORT}")
                self.listening.emit()
                self.changed.emit()
            except Exception as e:
                self.server_sock = None
                self.server_sockets = []
                self.is_listening = True
                utils.log_error(f"Unable to start server on TCP *:{BLENDER_PORT}", e)

    def stop_server(self):
        if self.server_sock:
            utils.log_info(f"Closing Server Socket")
            try:
                self.server_sock.shutdown()
                self.server_sock.close()
            except:
                pass
        self.is_listening = False
        self.server_sock = None
        self.server_sockets = []
        self.server_stopped.emit()
        self.changed.emit()

    def start_timer(self):
        self.time = time.time()
        if not self.timer:
            bpy.app.timers.register(self.loop, first_interval=TIMER_INTERVAL)
            self.timer = True
            utils.log_info(f"Service timer started")

    def stop_timer(self):
        if self.timer:
            try:
                bpy.app.timers.unregister(self.loop)
            except:
                pass
            self.timer = False
            utils.log_info(f"Service timer stopped")

    def try_start_client(self, host, port):
        link_props = bpy.context.scene.CCICLinkProps

        if not self.client_sock:
            utils.log_info(f"Attempting to connect")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(SOCKET_TIMEOUT)
                sock.connect((host, port))
                #sock.setblocking(False)
                self.is_connected = False
                link_props.connected = False
                self.is_connecting = True
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = host
                self.client_port = port
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"connecting with data link server on {host}:{port}")
                self.send_hello()
                self.connecting.emit()
                self.changed.emit()
                return True
            except:
                self.client_sock = None
                self.client_sockets = []
                self.is_connected = False
                link_props.connected = False
                self.is_connecting = False
                utils.log_info(f"Client socket connect failed!")
                return False
        else:
            utils.log_info(f"Client already connected!")
            return True

    def send_hello(self):
        self.local_app = "Blender"
        self.local_version = bpy.app.version_string
        self.local_path = get_local_data_path()
        json_data = {
            "Application": self.local_app,
            "Version": self.local_version,
            "Path": self.local_path
        }
        utils.log_info(f"Send Hello: {self.local_path}")
        self.send(OpCodes.HELLO, encode_from_json(json_data))

    def stop_client(self):
        link_props = bpy.context.scene.CCICLinkProps

        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            try:
                self.client_sock.shutdown()
                self.client_sock.close()
            except:
                pass
        self.is_connected = False
        self.is_connecting = False
        link_props.connected = False
        self.client_sock = None
        self.client_sockets = []
        if self.listening:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
        self.client_stopped.emit()
        self.changed.emit()

    def has_client_sock(self):
        if self.client_sock and (self.is_connected or self.is_connecting):
            return True
        else:
            return False

    def recv(self):
        link_props = bpy.context.scene.CCICLinkProps

        self.is_data = False
        self.is_import = False
        if self.has_client_sock():
            try:
                r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
            except Exception as e:
                utils.log_error("Client socket receive:select failed!", e)
                self.service_lost()
                return
            count = 0
            while r:
                op_code = None
                try:
                    header = self.client_sock.recv(8)
                    if header == 0:
                        utils.log_always("Socket closed by client")
                        self.service_lost()
                        return
                except Exception as e:
                    utils.log_error("Client socket receive:recv failed!", e)
                    self.service_lost()
                    return
                if header and len(header) == 8:
                    op_code, size = struct.unpack("!II", header)
                    data = None
                    if size > 0:
                        data = bytearray()
                        while size > 0:
                            chunk_size = min(size, MAX_CHUNK_SIZE)
                            try:
                                chunk = self.client_sock.recv(chunk_size)
                            except Exception as e:
                                utils.log_error("Client socket receive:chunk_recv failed!", e)
                                self.service_lost()
                                return
                            data.extend(chunk)
                            size -= len(chunk)
                    self.parse(op_code, data)
                    self.received.emit(op_code, data)
                    count += 1
                self.is_data = False
                # parse may have received a disconnect notice
                if not self.has_client_sock():
                    return
                # if preview sync every frame in sequence
                if op_code == OpCodes.SEQUENCE_FRAME and link_props.sequence_frame_sync:
                    self.is_data = True
                    return
                if op_code == OpCodes.CHARACTER or op_code == OpCodes.PROP:
                    # give imports time to process, otherwise bad things happen
                    self.is_data = False
                    self.is_import = True
                    return
                try:
                    r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                except Exception as e:
                    utils.log_error("Client socket receive:re-select failed!", e)
                    self.service_lost()
                    return
                if r:
                    self.is_data = True
                    if count >= MAX_RECEIVE or op_code == OpCodes.NOTIFY:
                        return

    def accept(self):
        link_props = bpy.context.scene.CCICLinkProps

        if self.server_sock and self.is_listening:
            r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)
            while r:
                try:
                    sock, address = self.server_sock.accept()
                except Exception as e:
                    utils.log_error("Server socket accept failed!", e)
                    self.service_lost()
                    return
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = address[0]
                self.client_port = address[1]
                self.is_connected = False
                self.is_connecting = True
                link_props.connected = False
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
                self.send_hello()
                self.accepted.emit(self.client_ip, self.client_port)
                self.changed.emit()
                r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)

    def parse(self, op_code, data):
        link_props = bpy.context.scene.CCICLinkProps
        self.keepalive_timer = KEEPALIVE_TIMEOUT_S

        if op_code == OpCodes.HELLO:
            utils.log_info(f"Hello Received")
            self.service_initialize()
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                self.remote_exe = json_data["Exe"]
                self.link_data.remote_app = self.remote_app
                self.link_data.remote_version = self.remote_version
                self.link_data.remote_path = self.remote_path
                self.link_data.remote_exe = self.remote_exe
                link_props.remote_app = self.remote_app
                link_props.remote_version = f"{self.remote_version[0]}.{self.remote_version[1]}.{self.remote_version[2]}"
                link_props.remote_path = self.remote_path
                link_props.remote_exe = self.remote_exe
                utils.log_always(f"Connected to: {self.remote_app} {self.remote_version}")
                utils.log_always(f"Using file path: {self.remote_path}")
                utils.log_always(f"Using exe path: {self.remote_exe}")

        elif op_code == OpCodes.PING:
            utils.log_info(f"Ping Received")

        elif op_code == OpCodes.STOP:
            utils.log_info(f"Termination Received")
            self.service_stop()

        elif op_code == OpCodes.DISCONNECT:
            utils.log_info(f"Disconnection Received")
            self.service_disconnect()

        elif op_code == OpCodes.NOTIFY:
            self.receive_notify(data)

        ##
        #

        elif op_code == OpCodes.SAVE:
            self.receive_save(data)

        elif op_code == OpCodes.TEMPLATE:
            self.receive_character_template(data)

        elif op_code == OpCodes.POSE:
            self.receive_pose(data)

        elif op_code == OpCodes.POSE_FRAME:
            self.receive_pose_frame(data)

        elif op_code == OpCodes.MORPH:
            self.receive_morph(data)

        elif op_code == OpCodes.MORPH_UPDATE:
            self.receive_morph(data, update=True)

        elif op_code == OpCodes.CHARACTER:
            self.receive_character_import(data)

        elif op_code == OpCodes.PROP:
            self.receive_character_import(data)

        elif op_code == OpCodes.CHARACTER_UPDATE:
            self.receive_actor_update(data)

        elif op_code == OpCodes.RIGIFY:
            self.receive_rigify_request(data)

        elif op_code == OpCodes.SEQUENCE:
            self.receive_sequence(data)

        elif op_code == OpCodes.SEQUENCE_FRAME:
            self.receive_sequence_frame(data)

        elif op_code == OpCodes.SEQUENCE_END:
            self.receive_sequence_end(data)

        elif op_code == OpCodes.SEQUENCE_ACK:
            self.receive_sequence_ack(data)

        elif op_code == OpCodes.LIGHTS:
            self.receive_lights(data)

        elif op_code == OpCodes.CAMERA_SYNC:
            self.receive_camera_sync(data)

        elif op_code == OpCodes.FRAME_SYNC:
            self.receive_frame_sync(data)


    def service_start(self, host, port):
        if not self.is_listening:
            self.start_timer()
            if SERVER_ONLY:
                self.start_server()
            else:
                if not self.try_start_client(host, port):
                    if not CLIENT_ONLY:
                        self.start_server()

    def service_initialize(self):
        link_props = bpy.context.scene.CCICLinkProps
        if self.is_connecting:
            self.is_connecting = False
            self.is_connected = True
            link_props.connected = True
            self.on_connected()
            self.connected.emit()
            self.changed.emit()

    def service_disconnect(self):
        self.send(OpCodes.DISCONNECT)
        if CLIENT_ONLY:
            self.stop_timer()
        self.stop_client()

    def service_stop(self):
        self.send(OpCodes.STOP)
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def service_lost(self):
        self.lost_connection.emit()
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def check_service(self):
        global LINK_SERVICE
        global LINK_DATA
        if not LINK_SERVICE or not LINK_DATA:
            utils.log_error("Datalink service data lost. Due to script reload?")
            utils.log_error("Connection is maintained but actor data has been reset.")
            LINK_SERVICE = self
            LINK_DATA = self.link_data
            LINK_DATA.reset()
        return True

    def check_paths(self):
        local_path = get_local_data_path()
        if local_path != self.local_path:
            self.local_path = local_path
            self.send_hello()

    def loop(self):
        current_time = time.time()
        delta_time = current_time - self.time
        self.time = current_time
        if delta_time > 0:
            rate = 1.0 / delta_time
            self.loop_rate = self.loop_rate * 0.75 + rate * 0.25
            #if self.loop_count % 100 == 0:
            #    utils.log_detail(f"LinkServer loop timer rate: {self.loop_rate}")
            self.loop_count += 1

        self.check_paths()

        if not self.check_service():
            return None

        if not self.timer:
            return None

        if self.is_connected:
            self.ping_timer -= delta_time
            self.keepalive_timer -= delta_time

            if USE_PING and self.ping_timer <= 0:
                self.send(OpCodes.PING)

            if USE_KEEPALIVE and self.keepalive_timer <= 0:
                utils.log_info("lost connection!")
                self.service_stop()
                return None

        elif self.is_listening:
            self.keepalive_timer -= delta_time

            if USE_KEEPALIVE and self.keepalive_timer <= 0:
                utils.log_info("no connection within time limit!")
                self.service_stop()
                return None

        # accept incoming connections
        self.accept()

        # receive client data
        self.recv()

        # run anything in sequence
        for i in range(0, self.sequence_send_count):
            self.sequence.emit()

        if self.is_import:
            return 0.5
        else:
            interval = 0.0 if (self.is_data or self.is_sequence) else TIMER_INTERVAL
            return interval

    def send(self, op_code, binary_data = None):
        if self.client_sock and (self.is_connected or self.is_connecting):
            try:
                data_length = len(binary_data) if binary_data else 0
                header = struct.pack("!II", op_code, data_length)
                data = bytearray()
                data.extend(header)
                if binary_data:
                    data.extend(binary_data)
                self.client_sock.sendall(data)
                self.ping_timer = PING_INTERVAL_S
                self.sent.emit()
            except Exception as e:
                utils.log_error("Client socket send failed!", e)
                self.service_lost()
                return

    def start_sequence(self, func=None):
        self.is_sequence = True
        self.sequence_send_count = 5
        self.sequence_send_rate = 5.0
        if func:
            self.sequence.connect(func)
        else:
            self.sequence.disconnect()

    def stop_sequence(self):
        self.is_sequence = False
        self.sequence.disconnect()

    def update_sequence(self, count, delta_frames):
        self.is_sequence = True
        if count is None:
            self.sequence_send_rate = 5.0
            self.sequence_send_count = 5
        else:
            self.sequence_send_rate = count
            self.sequence_send_count = count
            if self.loop_count % 30 == 0:
                utils.log_info(f"send_count: {self.sequence_send_count} delta_frames: {delta_frames}")


    def on_connected(self):
        self.send_notify("Connected")

    def send_notify(self, message):
        global LINK_SERVICE
        notify_json = { "message": message }
        LINK_SERVICE.send(OpCodes.NOTIFY, encode_from_json(notify_json))

    def receive_notify(self, data):
        notify_json = decode_to_json(data)
        update_link_status(notify_json["message"])

    def receive_save(self, data):
        if bpy.data.filepath:
            bpy.ops.wm.save_mainfile()

    def get_key_path(self, model_path, key_ext):
        dir, file = os.path.split(model_path)
        name, ext = os.path.splitext(file)
        key_path = os.path.normpath(os.path.join(dir, name + key_ext))
        return key_path

    def get_export_path(self, character_name, file_name):
        global LINK_SERVICE
        remote_path = LINK_SERVICE.remote_path
        local_path = LINK_SERVICE.local_path

        if not local_path:
            local_path = get_local_data_path()

        if local_path:
            export_folder = utils.make_sub_folder(local_path, "exports")
        else:
            export_folder = utils.make_sub_folder(remote_path, "exports")

        character_export_folder = utils.get_unique_folder_path(export_folder, character_name, create=True)
        export_path = os.path.join(character_export_folder, file_name)
        return export_path

    def get_selected_actors(self):
        global LINK_DATA
        props = bpy.context.scene.CC3ImportProps

        selected_objects = bpy.context.selected_objects
        avatars = props.get_avatars()
        actors = []
        cache_actors = []

        # if nothing selected then use the first available Avatar
        if not selected_objects and len(avatars) == 1:
            cache_actors.append(avatars[0])

        else:
            for obj in selected_objects:
                chr_cache = props.get_character_cache(obj, None)
                if chr_cache and chr_cache not in cache_actors:
                    cache_actors.append(chr_cache)

        for chr_cache in cache_actors:
            actor = LinkActor(chr_cache)
            actors.append(actor)

        return actors

    def get_active_actor(self):
        global LINK_DATA
        props = bpy.context.scene.CC3ImportProps
        active_object = utils.get_active_object()
        if active_object:
            chr_cache = props.get_character_cache(active_object, None)
            if chr_cache:
                actor = LinkActor(chr_cache)
                return actor
        return None

    def send_actor(self):
        global LINK_SERVICE
        actors = self.get_selected_actors()
        state = utils.store_mode_selection_state()
        utils.clear_selected_objects()
        actor: LinkActor
        utils.log_info(f"Sending LinkActors: {([a.name for a in actors])}")
        for actor in actors:
            self.send_notify(f"Blender Exporting: {actor.name}...")
            export_path = self.get_export_path(actor.name, actor.name + ".fbx")
            self.send_notify(f"Exporting: {actor.name}")
            bpy.ops.cc3.exporter(param="EXPORT_CC3", link_id_override=actor.get_link_id(), filepath=export_path)
            update_link_status(f"Sending: {actor.name}")
            export_data = encode_from_json({
                "path": export_path,
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
            })
            LINK_SERVICE.send(OpCodes.CHARACTER, export_data)
            update_link_status(f"Sent: {actor.name}")
        utils.restore_mode_selection_state(state)

    def send_morph(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            self.send_notify(f"Blender Exporting: {actor.name}...")
            export_path = self.get_export_path(actor.name, actor.name + "_morph.obj")
            key_path = self.get_key_path(export_path, ".ObjKey")
            self.send_notify(f"Exporting: {actor.name}")
            bpy.ops.cc3.exporter(param="EXPORT_CC3", filepath=export_path)
            update_link_status(f"Sending: {actor.name}")
            export_data = encode_from_json({
                "path": export_path,
                "key_path": key_path,
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
                "morph_name": "Test Morph",
                "morph_path": "Some/Path",
            })
            LINK_SERVICE.send(OpCodes.MORPH, export_data)
            update_link_status(f"Sent: {actor.name}")

    def encode_character_templates(self, actors: list):
        pose_bone: bpy.types.PoseBone
        actor_data = []
        character_template = {
            "count": len(actors),
            "actors": actor_data,
        }

        actor: LinkActor
        for actor in actors:
            chr_cache = actor.get_chr_cache()
            bones = []

            if chr_cache.rigified:
                # add the export retarget rig
                if utils.object_exists_is_armature(chr_cache.rig_export_rig):
                    export_rig = chr_cache.rig_export_rig
                else:
                    export_rig = rigging.adv_export_pair_rigs(chr_cache, link_target=True)[0]
                # get all the exportable deformation bones
                if rigutils.select_rig(export_rig):
                    for pose_bone in export_rig.pose.bones:
                        if pose_bone.name != "root" and not pose_bone.name.startswith("DEF-"):
                            bones.append(pose_bone.name)
            else:
                # get all the bones
                rig: bpy.types.Object = chr_cache.get_armature()
                if rigutils.select_rig(rig):
                    for pose_bone in rig.pose.bones:
                        bones.append(pose_bone.name)

            actor.collect_shape_keys()
            shapes = [key for key in actor.shape_keys]

            actor.bones = bones
            actor_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
                "bones": bones,
                "shapes": shapes,
            })

        return encode_from_json(character_template)

    def encode_pose_data(self, actors):
        fps = bpy.context.scene.render.fps
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end
        start_time = start_frame / fps
        end_time = end_frame / fps
        frame = bpy.context.scene.frame_current
        time = frame / fps
        actors_data = []
        data = {
            "fps": fps,
            "start_time": start_time,
            "end_time": end_time,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "time": time,
            "frame": frame,
            "actors": actors_data,
        }
        actor: LinkActor
        for actor in actors:
            actors_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
            })
        return encode_from_json(data)

    def encode_pose_frame_data(self, actors: list):
        pose_bone: bpy.types.PoseBone
        data = bytearray()
        data += struct.pack("!II", len(actors), bpy.context.scene.frame_current)
        actor: LinkActor
        for actor in actors:
            data += pack_string(actor.name)
            data += pack_string(actor.get_type())
            data += pack_string(actor.get_link_id())
            chr_cache = actor.get_chr_cache()

            if chr_cache.rigified:
                # add the import retarget rig
                if utils.object_exists_is_armature(chr_cache.rig_export_rig):
                    export_rig = chr_cache.rig_export_rig
                else:
                    export_rig = rigging.adv_export_pair_rigs(chr_cache, link_target=True)[0]
                M: Matrix = export_rig.matrix_world

                # pack object transform
                T: Matrix = M
                t = T.to_translation() * 100
                r = T.to_quaternion()
                s = T.to_scale()
                data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

                # pack all the bone data for the exportable deformation bones
                data += struct.pack("!I", len(actor.bones))
                if utils.object_mode_to(export_rig):
                    for bone_name in actor.bones:
                        pose_bone = export_rig.pose.bones[bone_name]
                        T: Matrix = M @ pose_bone.matrix
                        t = T.to_translation() * 100
                        r = T.to_quaternion()
                        s = T.to_scale()
                        data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
            else:
                rig: bpy.types.Object = chr_cache.get_armature()
                M: Matrix = rig.matrix_world

                # pack object transform
                T: Matrix = M
                t = T.to_translation() * 100
                r = T.to_quaternion()
                s = T.to_scale()
                data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

                # pack all the bone data
                data += struct.pack("!I", len(rig.pose.bones))
                if utils.object_mode_to(rig):
                    pose_bone: bpy.types.PoseBone
                    for pose_bone in rig.pose.bones:
                        T: Matrix = M @ pose_bone.matrix
                        t = T.to_translation()
                        r = T.to_quaternion()
                        s = T.to_scale()
                        data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

            # pack shape_keys
            data += struct.pack("!I", len(actor.shape_keys))
            for shape_key, key in actor.shape_keys.items():
                data += struct.pack("!f", key.value)

        return data

    def encode_sequence_data(self, actors):
        fps = bpy.context.scene.render.fps
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end
        start_time = start_frame / fps
        end_time = end_frame / fps
        actors_data = []
        data = {
            "fps": fps,
            "start_time": start_time,
            "end_time": end_time,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "actors": actors_data,
        }
        actor: LinkActor
        for actor in actors:
            actors_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
            })
        return encode_from_json(data)

    def send_pose(self):
        global LINK_SERVICE
        global LINK_DATA

        # get actors
        actors = self.get_selected_actors()
        if actors:
            mode_selection = utils.store_mode_selection_state()
            update_link_status(f"Sending Current Pose Set")
            self.send_notify(f"Pose Set")
            # send pose info
            pose_data = self.encode_pose_data(actors)
            LINK_SERVICE.send(OpCodes.POSE, pose_data)
            # send template data first
            template_data = self.encode_character_templates(actors)
            LINK_SERVICE.send(OpCodes.TEMPLATE, template_data)
            # store the actors
            LINK_DATA.sequence_actors = actors
            # force recalculate all transforms
            bpy.context.view_layer.update()
            # send pose data
            pose_frame_data = self.encode_pose_frame_data(actors)
            LINK_SERVICE.send(OpCodes.POSE_FRAME, pose_frame_data)
            # clear the actors
            LINK_DATA.sequence_actors = None
            # restore
            utils.restore_mode_selection_state(mode_selection)

    def send_animation(self):
        return

    def send_sequence(self):
        global LINK_SERVICE
        global LINK_DATA

        # get actors
        actors = self.get_selected_actors()
        if actors:
            update_link_status(f"Sending Animation Sequence")
            self.send_notify(f"Animation Sequence")
            # reset animation to start
            bpy.context.scene.frame_current = bpy.context.scene.frame_start
            LINK_DATA.sequence_current_frame = bpy.context.scene.frame_current
            # send animation meta data
            sequence_data = self.encode_sequence_data(actors)
            LINK_SERVICE.send(OpCodes.SEQUENCE, sequence_data)
            # send template data first
            template_data = self.encode_character_templates(actors)
            LINK_SERVICE.send(OpCodes.TEMPLATE, template_data)
            # store the actors
            LINK_DATA.sequence_actors = actors
            # start the sending sequence
            LINK_SERVICE.start_sequence(self.send_sequence_frame)

    def send_sequence_frame(self):
        global LINK_SERVICE
        global LINK_DATA

        # set/fetch the current frame in the sequence
        current_frame = ensure_current_frame(LINK_DATA.sequence_current_frame)
        update_link_status(f"Sequence Frame: {current_frame}")
        # force recalculate all transforms
        bpy.context.view_layer.update()
        # send current sequence frame pose
        pose_data = self.encode_pose_frame_data(LINK_DATA.sequence_actors)
        LINK_SERVICE.send(OpCodes.SEQUENCE_FRAME, pose_data)
        # check for end
        if current_frame >= bpy.context.scene.frame_end:
            LINK_SERVICE.stop_sequence()
            self.send_sequence_end()
            return
        # advance to next frame now
        LINK_DATA.sequence_current_frame = next_frame(current_frame)


    def send_sequence_end(self):
        # clear the actors
        LINK_DATA.sequence_actors = None
        LINK_SERVICE.send(OpCodes.SEQUENCE_END)

    def decode_pose_frame_header(self, pose_data):
        count, frame = struct.unpack_from("!II", pose_data)
        LINK_DATA.sequence_current_frame = frame
        return frame

    def decode_pose_frame_data(self, pose_data):
        global LINK_DATA
        link_props = bpy.context.scene.CCICLinkProps

        offset = 0
        count, frame = struct.unpack_from("!II", pose_data, offset)
        ensure_current_frame(frame)
        LINK_DATA.sequence_current_frame = frame
        offset = 8
        actors = []
        for i in range(0, count):
            offset, name = unpack_string(pose_data, offset)
            offset, character_type = unpack_string(pose_data, offset)
            offset, link_id = unpack_string(pose_data, offset)
            actor = LINK_DATA.find_sequence_actor(link_id)
            actor_ready = False
            if actor:
                objects = actor.get_sequence_objects()
                rig: bpy.types.Object = actor.get_armature()
                actor_ready = actor.ready()
                is_prop = actor.get_type() == "PROP"
            else:
                objects = []
                rig = None
                is_prop = False

            # unpack rig transform
            tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
            offset += 40
            if rig:
                loc = Vector((tx, ty, tz)) * 0.01
                rot = Quaternion((rw, rx, ry, rz))
                sca = Vector((sx, sy, sz))
                # don't update the character rig transform
                # this way the user can place the objects wherever and the animation
                # will be build around this reference as the root bone and object transform
                # are the same thing in iClone/CC4, but not in Blender.
                #rig.location = loc
                #rig.rotation_mode = "QUATERNION"
                #rig.rotation_quaternion = rot
                #rig.location = Vector((0,0,0))
                #rig.rotation_mode = "QUATERNION"
                #rig.rotation_quaternion = Quaternion((1,0,0,0))

            datalink_rig = None
            if actor:
                if actor_ready:
                    actors.append(actor)
                    datalink_rig = make_datalink_import_rig(actor)
                else:
                    utils.log_error(f"Actor not ready: {name}/ {link_id}")
            else:
                utils.log_error(f"Could not find actor: {name}/ {link_id}")

            # unpack bone transforms
            num_bones = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4

            # unpack the binary transform data directly into the datalink rig pose bones
            for i in range(0, num_bones):
                tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
                offset += 40
                if actor and datalink_rig:
                    bone_name = actor.rig_bones[i]
                    pose_bone: bpy.types.PoseBone = datalink_rig.pose.bones[bone_name]
                    loc = Vector((tx, ty, tz)) * 0.01
                    rot = Quaternion((rw, rx, ry, rz))
                    sca = Vector((sx, sy, sz))
                    pose_bone.rotation_mode = "QUATERNION"
                    pose_bone.rotation_quaternion = rot
                    pose_bone.location = loc
                    pose_bone.scale = sca

            # unpack mesh transforms
            num_meshes = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4

            # unpack the binary transform data directly into the mesh transform
            for i in range(0, num_meshes):
                tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
                offset += 40
                if actor and datalink_rig:
                    mesh_name = actor.meshes[i]
                    if mesh_name in actor.skin_meshes:
                        obj = actor.skin_meshes[mesh_name][0]
                        actor.skin_meshes[mesh_name][1] = Vector((tx, ty, tz)) * 0.01
                        actor.skin_meshes[mesh_name][2] = Quaternion((rw, rx, ry, rz))
                        actor.skin_meshes[mesh_name][3] = Vector((sx, sy, sz))


            # unpack the expression shape keys into the mesh objects
            num_weights = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4
            expression_weights = [0] * num_weights
            for i in range(0, num_weights):
                weight = struct.unpack_from("!f", pose_data, offset)[0]
                offset += 4
                if actor and objects and link_props.sequence_preview_shape_keys:
                    expression_name = actor.expressions[i]
                    set_actor_expression_weight(objects, expression_name, weight)
                expression_weights[i] = weight

            # unpack the viseme shape keys into the mesh objects
            num_weights = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4
            viseme_weights = [0] * num_weights
            for i in range(0, num_weights):
                weight = struct.unpack_from("!f", pose_data, offset)[0]
                offset += 4
                if actor and objects and link_props.sequence_preview_shape_keys:
                    viseme_name = actor.visemes[i]
                    set_actor_viseme_weight(objects, viseme_name, weight)
                viseme_weights[i] = weight

            # TODO: morph weights
            morph_weights = []

            # store shape keys in the cache
            if actor_ready:
                store_shape_key_cache_keyframes(actor, frame, expression_weights, viseme_weights, morph_weights)

        return actors

    def reposition_prop_meshes(self, actors):
        actor: LinkActor
        for actor in actors:
            for mesh_name in actor.skin_meshes:
                obj, loc, rot, sca = actor.skin_meshes[mesh_name]
                rig = obj.parent
                obj.matrix_world = utils.make_transform_matrix(loc, rot, rig.scale)

    def find_link_id(self, link_id: str):
        for obj in bpy.data.objects:
            if "link_id" in obj and obj["link_id"] == link_id:
                return obj
        return None

    def add_spot_light(self, name):
        bpy.ops.object.light_add(type="SPOT")
        light = bpy.context.active_object
        light.name = name
        return light

    def add_area_light(self, name):
        bpy.ops.object.light_add(type="AREA")
        light = bpy.context.active_object
        light.name = name
        return light

    def add_point_light(self, name):
        bpy.ops.object.light_add(type="POINT")
        light = bpy.context.active_object
        light.name = name
        return light

    def add_dir_light(self, name):
        bpy.ops.object.light_add(type="SUN")
        light = bpy.context.active_object
        light.name = name
        return light

    def decode_lights_data(self, data):
        lights_data = decode_to_json(data)

        RECTANGULAR_SPOTLIGHTS_AS_AREA = False

        for light_data in lights_data["lights"]:

            is_dir = light_data["type"] == "DIR"
            is_point = light_data["type"] == "POINT" and light_data["is_rectangle"] == False and light_data["is_tube"] == False
            if RECTANGULAR_SPOTLIGHTS_AS_AREA:
                is_area = ((light_data["type"] == "POINT" and (light_data["is_rectangle"] == True or light_data["is_tube"] == True))
                        or (light_data["type"] == "SPOT" and light_data["is_rectangle"] == True))
                is_spot = light_data["type"] == "SPOT" and light_data["is_rectangle"] == False
            else:
                is_area = (light_data["type"] == "POINT" and (light_data["is_rectangle"] == True or light_data["is_tube"] == True))
                is_spot = light_data["type"] == "SPOT"

            light_type = "SUN" if is_dir else "AREA" if is_area else "POINT" if is_point else "SPOT"

            light = self.find_link_id(light_data["link_id"])
            if light and (light.type != "LIGHT" or light.data.type != light_type):
                utils.delete_light_object(light)
                light = None
            if not light:
                if is_area:
                    light = self.add_area_light(light_data["name"])
                elif is_point:
                    light = self.add_point_light(light_data["name"])
                elif is_dir:
                    light = self.add_dir_light(light_data["name"])
                else:
                    light = self.add_spot_light(light_data["name"])
                light["link_id"] = light_data["link_id"]

            light.location = utils.array_to_vector(light_data["loc"]) / 100
            light.rotation_mode = "QUATERNION"
            light.rotation_quaternion = utils.array_to_quaternion(light_data["rot"])
            light.scale = utils.array_to_vector(light_data["sca"])
            light.data.color = utils.array_to_color(light_data["color"], False)
            mult = light_data["multiplier"]
            #if mult > 10:
            #    mult *= (1 + pow((mult - 10)/90, 1.5))
            if is_dir:
                light.data.energy = 450 * pow(light_data["multiplier"]/20, 2)
            elif is_spot:
                light.data.energy = 40.0 * mult
            elif is_point:
                light.data.energy = 40.0 * mult
            elif is_area:
                light.data.energy = 10.0 * mult
            if not is_dir:
                light.data.use_custom_distance = True
                light.data.cutoff_distance = light_data["range"] / 100
            if is_spot:
                light.data.spot_size = light_data["angle"] * 0.01745329
                light.data.spot_blend = 0.01 * light_data["falloff"] * (0.5 + 0.01 * light_data["attenuation"] * 0.5)
                if light_data["is_rectangle"]:
                    light.data.shadow_soft_size = (light_data["rect"][0] + light_data["rect"][0]) / 200
                elif light_data["is_tube"]:
                    light.data.shadow_soft_size = light_data["tube_radius"] / 100
            if is_area:
                if light_data["is_rectangle"]:
                    light.data.shape = "RECTANGLE"
                    light.data.size = light_data["rect"][0] / 100
                    light.data.size_y = light_data["rect"][1] / 100
                elif light_data["is_tube"]:
                    light.data.shape = "DISK"
                    light.data.size = light_data["tube_radius"] / 100
            light.data.use_shadow = light_data["cast_shadow"]
            if light_data["cast_shadow"]:
                if not is_dir:
                    light.data.shadow_buffer_clip_start = 0.0025
                    light.data.shadow_buffer_bias = 1.0
                light.data.use_contact_shadow = True
                light.data.contact_shadow_distance = 0.05
                light.data.contact_shadow_thickness = 0.0025
            light.hide_set(not light_data["active"])

        # clean up lights not found in scene
        for obj in bpy.data.objects:
            if obj.type == "LIGHT":
               if "link_id" in obj and obj["link_id"] not in lights_data["scene_lights"]:
                   utils.delete_light_object(obj)
        #
        bpy.context.scene.eevee.use_gtao = True
        bpy.context.scene.eevee.gtao_distance = 0.25
        bpy.context.scene.eevee.gtao_factor = 0.5
        bpy.context.scene.eevee.use_bloom = True
        bpy.context.scene.eevee.bloom_threshold = 0.8
        bpy.context.scene.eevee.bloom_knee = 0.5
        bpy.context.scene.eevee.bloom_radius = 2.0
        bpy.context.scene.eevee.bloom_intensity = 1.0
        bpy.context.scene.eevee.use_ssr = True
        bpy.context.scene.eevee.use_ssr_refraction = True
        bpy.context.scene.eevee.bokeh_max_size = 32
        colorspace.set_view_settings("Filmic", "High Contrast", 0, 0.75)
        if bpy.context.scene.cycles.transparent_max_bounces < 50:
            bpy.context.scene.cycles.transparent_max_bounces = 50
        view_space: bpy.types.Area = self.get_view_space()
        if view_space:
            view_space.shading.type = 'MATERIAL'
            view_space.shading.use_scene_lights = True
            view_space.shading.use_scene_world = False
            view_space.shading.studio_light = 'studio.exr'
            view_space.shading.studiolight_rotate_z = 0.0 * 0.01745329
            view_space.shading.studiolight_intensity = 0.2
            view_space.shading.studiolight_background_alpha = 0.0
            view_space.shading.studiolight_background_blur = 0.5
            if LINK_SERVICE.is_cc():
                # only hide the lights if it's from Character Creator
                view_space.overlay.show_extras = False

    def receive_lights(self, data):
        update_link_status(f"Light Data Receveived")
        self.decode_lights_data(data)


    # Camera
    #

    def get_region_3d(self):
        space = self.get_view_space()
        if space:
            return space, space.region_3d
        return None, None

    def get_view_space(self):
        area = self.get_view_area()
        if area:
            return area.spaces.active
        return None

    def get_view_area(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                return area
        return None

    def get_view_camera_data(self):
        view_space: bpy.types.Space
        r3d: bpy.types.RegionView3D
        view_space, r3d = self.get_region_3d()
        t = r3d.view_location
        r = r3d.view_rotation
        d = r3d.view_distance
        dir = Vector((0,0,-1))
        dir.rotate(r)
        loc: Vector = t - (dir * d)
        lens = view_space.lens
        data = {
            "link_id": "0",
            "name": "Viewport Camera",
            "loc": [loc.x, loc.y, loc.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [1, 1, 1],
            "focal_length": lens,
        }
        return data

    def get_view_camera_pivot(self):
        view_space, r3d = self.get_region_3d()
        t = r3d.view_location
        return t

    def send_camera_sync(self):
        global LINK_SERVICE
        #
        update_link_status(f"Synchronizing View Camera")
        self.send_notify(f"Sync View Camera")
        camera_data = self.get_view_camera_data()
        pivot = self.get_view_camera_pivot()
        data = {
            "view_camera": camera_data,
            "pivot": [pivot.x, pivot.y, pivot.z],
        }
        LINK_SERVICE.send(OpCodes.CAMERA_SYNC, encode_from_json(data))

    def decode_camera_sync_data(self, data):
        data = decode_to_json(data)
        camera_data = data["view_camera"]
        pivot = utils.array_to_vector(data["pivot"]) / 100
        view_space, r3d = self.get_region_3d()
        loc = utils.array_to_vector(camera_data["loc"]) / 100
        rot = utils.array_to_quaternion(camera_data["rot"])
        to_pivot = pivot - loc
        dir = Vector((0,0,-1))
        dir.rotate(rot)
        dist = to_pivot.dot(dir)
        if dist <= 0:
            dist = 1.0
        r3d.view_location = loc + dir * dist
        r3d.view_rotation = rot
        r3d.view_distance = dist
        view_space.lens = camera_data["focal_length"]

    def receive_camera_sync(self, data):
        update_link_status(f"Camera Data Receveived")
        self.decode_camera_sync_data(data)

    def send_frame_sync(self):
        update_link_status(f"Sending Frame Sync")
        fps = bpy.context.scene.render.fps
        start_frame = bpy.context.scene.frame_start
        end_frame = bpy.context.scene.frame_end
        current_frame = bpy.context.scene.frame_current
        start_time = start_frame / fps
        end_time = end_frame / fps
        current_time = current_frame / fps
        frame_data = {
            "fps": fps,
            "start_time": start_time,
            "end_time": end_time,
            "current_time": current_time,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "current_frame": current_frame,
        }
        self.send(OpCodes.FRAME_SYNC, encode_from_json(frame_data))

    def receive_frame_sync(self, data):
        update_link_status(f"Frame Sync Receveived")
        frame_data = decode_to_json(data)
        start_frame = frame_data["start_frame"]
        end_frame = frame_data["end_frame"]
        current_frame = frame_data["current_frame"]
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame
        bpy.context.scene.frame_current = current_frame


    # Character Pose
    #

    def receive_character_template(self, data):
        global LINK_DATA

        # decode character templates
        template_json = decode_to_json(data)
        count = template_json["count"]
        utils.log_info(f"Receive Character Template: {count} actors")

        # fetch actors and set templates
        for actor_data in template_json["actors"]:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LINK_DATA.find_sequence_actor(link_id)
            if actor:
                actor.set_template(actor_data["bones"],
                                   actor_data["meshes"],
                                   actor_data["expressions"],
                                   actor_data["visemes"],
                                   actor_data["morphs"])
                utils.log_info(f"Preparing Actor: {actor.name} ({actor.get_link_id()})")
                prep_rig(actor, LINK_DATA.sequence_start_frame, LINK_DATA.sequence_end_frame)
            else:
                utils.log_error(f"Unable to find actor: {name} ({link_id})")

        update_link_status(f"Character Templates Received")

    def select_actor_rigs(self, actors, start_frame=0, end_frame=0):
        rigs = []
        actor: LinkActor
        for actor in actors:
            rig = actor.get_armature()
            if rig:
                rigs.append(rig)
        if rigs:
            all_selected = True
            if not (utils.get_mode() == "POSE" and len(bpy.context.selected_objects) == len(rigs)):
                all_selected = False
            else:
                for rig in rigs:
                    if rig not in bpy.context.selected_objects:
                        all_selected = False
                        break
            if not all_selected:
                utils.set_mode("OBJECT")
                utils.clear_selected_objects()
                utils.try_select_objects(rigs, True, make_active=True)
                utils.set_mode("POSE")
        return rigs

    def receive_pose(self, data):
        global LINK_SERVICE
        global LINK_DATA

        # decode pose data
        json_data = decode_to_json(data)
        start_frame = json_data["start_frame"]
        end_frame = json_data["end_frame"]
        frame = json_data["frame"]
        LINK_DATA.sequence_start_frame = frame
        LINK_DATA.sequence_end_frame = frame
        LINK_DATA.sequence_current_frame = frame
        utils.log_info(f"Receive Pose: {frame}")

        # fetch actors
        actors_data = json_data["actors"]
        actors = []
        for actor_data in actors_data:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
            if actor:
                actors.append(actor)

        # set pose frame
        update_link_status(f"Receiving Pose Frame: {frame}")
        LINK_DATA.sequence_actors = actors
        bpy.ops.screen.animation_cancel()
        set_frame_range(start_frame, end_frame)
        set_frame(frame)

    def receive_pose_frame(self, data):
        global LINK_DATA

        # decode and cache pose
        frame = self.decode_pose_frame_header(data)
        utils.log_info(f"Receive Pose Frame: {frame}")
        actors = self.decode_pose_frame_data(data)

        # force recalculate all transforms
        bpy.context.view_layer.update()

        #self.reposition_prop_meshes(actors)

        # store frame data
        update_link_status(f"Pose Frame: {frame}")
        rigs = self.select_actor_rigs(actors)
        if rigs:
            for actor in actors:
                if actor.ready():
                    store_bone_cache_keyframes(actor, frame)

            # write pose action
            for actor in actors:
                if actor.ready():
                    remove_datalink_import_rig(actor)
                    write_sequence_actions(actor)
                    pass

        # finish
        LINK_DATA.sequence_actors = None
        bpy.context.scene.frame_current = frame

    def receive_sequence(self, data):
        global LINK_SERVICE
        global LINK_DATA

        # decode sequence data
        json_data = decode_to_json(data)
        start_frame = json_data["start_frame"]
        end_frame = json_data["end_frame"]
        LINK_DATA.sequence_start_frame = start_frame
        LINK_DATA.sequence_end_frame = end_frame
        LINK_DATA.sequence_current_frame = start_frame
        num_frames = end_frame - start_frame + 1
        utils.log_info(f"Receive Sequence: {start_frame} to {end_frame}, {num_frames} frames")

        # fetch sequence actors
        actors_data = json_data["actors"]
        actors = []
        for actor_data in actors_data:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
            if actor:
                actors.append(actor)
        LINK_DATA.sequence_actors = actors

        # update scene range
        update_link_status(f"Receiving Live Sequence: {num_frames} frames")
        bpy.ops.screen.animation_cancel()
        set_frame_range(LINK_DATA.sequence_start_frame, LINK_DATA.sequence_end_frame)
        set_frame(LINK_DATA.sequence_start_frame)

        # start the sequence
        LINK_SERVICE.start_sequence()

    def receive_sequence_frame(self, data):
        global LINK_SERVICE
        global LINK_DATA

        # decode and cache pose
        frame = self.decode_pose_frame_header(data)
        utils.log_detail(f"Receive Sequence Frame: {frame}")
        actors = self.decode_pose_frame_data(data)

        # force recalculate all transforms
        bpy.context.view_layer.update()

        #self.reposition_prop_meshes(actors)

        # store frame data
        update_link_status(f"Sequence Frame: {LINK_DATA.sequence_current_frame}")
        rigs = self.select_actor_rigs(actors)
        if rigs:
            for actor in actors:
                store_bone_cache_keyframes(actor, frame)

        # send sequence frame ack
        self.send_sequence_ack(frame)

    def send_sequence_ack(self, frame):
        global LINK_SERVICE
        global LINK_DATA
        # encode sequence ack
        data = encode_from_json({
            "frame": frame,
            "rate": LINK_SERVICE.loop_rate,
        })
        # send sequence ack
        LINK_SERVICE.send(OpCodes.SEQUENCE_ACK, data)

    def receive_sequence_end(self, data):
        global LINK_SERVICE
        global LINK_DATA

        # decode sequence end
        json_data = decode_to_json(data)
        actors_data = json_data["actors"]
        utils.log_info("Receive Sequence End")

        # fetch actors
        actors = []
        actor: LinkActor
        for actor_data in actors_data:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LINK_DATA.find_sequence_actor(link_id)
            if actor:
                actors.append(actor)
        num_frames = LINK_DATA.sequence_end_frame - LINK_DATA.sequence_start_frame + 1
        update_link_status(f"Live Sequence Complete: {num_frames} frames")

        # write actions
        for actor in actors:
            remove_datalink_import_rig(actor)
            write_sequence_actions(actor)

        # stop sequence
        LINK_SERVICE.stop_sequence()
        LINK_DATA.sequence_actors = None
        bpy.context.scene.frame_current = LINK_DATA.sequence_start_frame

        # play the recorded sequence
        bpy.ops.screen.animation_play()

    def receive_sequence_ack(self, data):
        link_props = bpy.context.scene.CCICLinkProps
        global LINK_DATA

        json_data = decode_to_json(data)
        ack_frame = json_data["frame"]
        server_rate = json_data["rate"]
        delta_frames = LINK_DATA.sequence_current_frame - ack_frame
        if link_props.match_client_rate:
            if LINK_DATA.ack_time == 0.0:
                LINK_DATA.ack_time = time.time()
                LINK_DATA.ack_rate = 120
                count = 5
            else:
                t = time.time()
                delta_time = max(t - LINK_DATA.ack_time, 1/120)
                LINK_DATA.ack_time = t
                ack_rate = (1.0 / delta_time)
                LINK_DATA.ack_rate = utils.lerp(LINK_DATA.ack_rate, ack_rate, 0.5)

                if delta_frames >= 20:
                    count = 0
                elif delta_frames >= 10:
                    count = 1
                elif delta_frames >= 5:
                    count = 2
                else:
                    count = 4

            self.update_sequence(count, delta_frames)
        else:
            self.update_sequence(5, delta_frames)

    def receive_character_import(self, data):
        props = bpy.context.scene.CC3ImportProps
        global LINK_DATA

        # decode character import data
        json_data = decode_to_json(data)
        fbx_path = json_data["path"]
        name = json_data["name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]

        utils.log_info(f"Receive Character Import: {name} / {link_id} / {fbx_path}")

        actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
        if actor:
            update_link_status(f"Character: {name} exists!")
            utils.log_info(f"Actor {name} ({link_id}) already exists!")
            return

        update_link_status(f"Receving Character Import: {name}")
        if os.path.exists(fbx_path):
            try:
                bpy.ops.cc3.importer(param="IMPORT", filepath=fbx_path, link_id=link_id)
            except:
                utils.log_error(f"Error importing {fbx_path}")
                return
            actor = LinkActor.find_actor(link_id)
            # props have big ugly bones, so show them as wires
            if actor and actor.get_type() == "PROP":
                arm = actor.get_armature()
                if arm:
                    arm.data.display_type = "WIRE"
            update_link_status(f"Character Imported: {actor.name}")

    def receive_actor_update(self, data):
        global LINK_DATA

        # decode character update
        json_data = decode_to_json(data)
        old_name = json_data["old_name"]
        old_link_id = json_data["old_link_id"]
        character_type = json_data["type"]
        new_name = json_data["new_name"]
        new_link_id = json_data["new_link_id"]
        utils.log_info(f"Receive Character Update: {old_name} -> {new_name} / {old_link_id} -> {new_link_id}")

        # update character data
        actor = LinkActor.find_actor(old_link_id, search_name=old_name, search_type=character_type)
        utils.log_info(f"Updating Actor: {actor.name} {actor.get_link_id()}")
        actor.update_name(new_name)
        actor.update_link_id(new_link_id)

    def receive_morph(self, data, update=False):
        global LINK_DATA

        # decode receive morph
        json_data = decode_to_json(data)
        obj_path = json_data["path"]
        name = json_data["name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        utils.log_info(f"Receive Character Morph: {name} / {link_id} / {obj_path}")

        # fetch actor to update morph or import new morph character
        actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
        if actor:
            update = True
        else:
            update = False
        update_link_status(f"Receving Character Morph: {name}")
        if os.path.exists(obj_path):
            if update:
                self.import_morph_update(actor, obj_path)
                update_link_status(f"Morph Updated: {actor.name}")
            else:
                bpy.ops.cc3.importer(param="IMPORT", filepath=obj_path, link_id=link_id)
                actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
                update_link_status(f"Morph Imported: {actor.name}")

    def import_morph_update(self, actor: LinkActor, file_path):
        utils.log_info(f"Import Morph Update: {actor.name} / {file_path}")

        utils.tag_objects()
        importer.obj_import(file_path, split_objects=False, split_groups=False, vgroups=True)
        objects = utils.untagged_objects()
        if objects and actor and actor.get_chr_cache():
            for source in objects:
                source.scale = (0.01, 0.01, 0.01)
                dest = actor.get_chr_cache().object_cache[0].object
                geom.copy_vert_positions_by_index(source, dest)
                utils.delete_mesh_object(source)

    def receive_rigify_request(self, data):
        global LINK_SERVICE

        # decode rigify request
        json_data = decode_to_json(data)
        name = json_data["name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        utils.log_info(f"Receive Rigify Request: {name} / {link_id}")

        # rigify actor armature
        actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
        if actor:
            chr_cache = actor.get_chr_cache()
            if chr_cache:
                if chr_cache.rigified:
                    utils.log_error(f"Character {actor.name} already rigified!")
                    return
                update_link_status(f"Rigifying: {actor.name}")
                chr_cache.select()
                bpy.ops.cc3.rigifier(param="ALL", no_face_rig=True)
                update_link_status(f"Character Rigified: {actor.name}")






LINK_SERVICE: LinkService = None


def get_link_service():
    global LINK_SERVICE
    return LINK_SERVICE


def link_state_update():
    global LINK_SERVICE
    if LINK_SERVICE:
        link_props = bpy.context.scene.CCICLinkProps
        link_props.link_listening = LINK_SERVICE.is_listening
        link_props.link_connected = LINK_SERVICE.is_connected
        link_props.link_connecting = LINK_SERVICE.is_connecting
        utils.update_ui()


def update_link_status(text):
    link_props = bpy.context.scene.CCICLinkProps
    link_props.link_status = text
    utils.update_ui()


def reconnect():
    global LINK_SERVICE
    link_props = bpy.context.scene.CCICLinkProps
    if link_props.connected:
        if LINK_SERVICE and LINK_SERVICE.is_connected:
            utils.log_info("Datalink remains connected.")
        elif not LINK_SERVICE or not LINK_SERVICE.is_connected:
            utils.log_info("Datalink was connected. Attempting to reconnect...")
            bpy.ops.ccic.datalink(param="START")


class CCICDataLink(bpy.types.Operator):
    """Data Link Control Operator"""
    bl_idname = "ccic.datalink"
    bl_label = "Listener"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        global LINK_SERVICE

        if self.param == "START":
            self.link_start()
            return {'FINISHED'}

        elif self.param == "DISCONNECT":
            self.link_disconnect()
            return {'FINISHED'}

        elif self.param == "STOP":
            self.link_stop()
            return {'FINISHED'}

        if self.param in ["SEND_POSE", "SEND_ANIM", "SEND_ACTOR", "SEND_MORPH", "SYNC_CAMERA"]:
            if not LINK_SERVICE or not LINK_SERVICE.is_connected:
                self.link_start()
            if not LINK_SERVICE or not (LINK_SERVICE.is_connected or LINK_SERVICE.is_connecting):
                self.report({"ERROR"}, "Server not listening!")
                return {'FINISHED'}

        if LINK_SERVICE:

            if self.param == "SEND_POSE":
                LINK_SERVICE.send_pose()
                return {'FINISHED'}

            elif self.param == "SEND_ANIM":
                LINK_SERVICE.send_sequence()
                return {'FINISHED'}

            elif self.param == "SEND_ACTOR":
                LINK_SERVICE.send_actor()
                return {'FINISHED'}

            elif self.param == "SEND_MORPH":
                LINK_SERVICE.send_morph()
                return {'FINISHED'}

            elif self.param == "SYNC_CAMERA":
                LINK_SERVICE.send_camera_sync()
                return {'FINISHED'}

            elif self.param == "TEST":
                LINK_SERVICE.stop_client()
                return {'FINISHED'}

            elif self.param == "SHOW_ACTOR_FILES":
                props = bpy.context.scene.CC3ImportProps
                chr_cache = props.get_context_character_cache(context)
                if chr_cache:
                    utils.open_folder(chr_cache.get_import_dir())
                return {'FINISHED'}

            elif self.param == "SHOW_PROJECT_FILES":
                local_path = get_local_data_path()
                if local_path:
                    utils.open_folder(local_path)
                return {'FINISHED'}

        return {'FINISHED'}

    def prep_local_files(self):
        data_path = get_local_data_path()
        if data_path:
            os.makedirs(data_path, exist_ok=True)
            import_path = os.path.join(data_path, "imports")
            export_path = os.path.join(data_path, "exports")
            os.makedirs(import_path, exist_ok=True)
            os.makedirs(export_path, exist_ok=True)

    def link_start(self, is_go_b=False):
        link_props = bpy.context.scene.CCICLinkProps
        global LINK_SERVICE

        self.prep_local_files()
        if not LINK_SERVICE:
            LINK_SERVICE = LinkService()
            LINK_SERVICE.changed.connect(link_state_update)

        if LINK_SERVICE:
            LINK_SERVICE.service_start(link_props.link_host_ip, link_props.link_port)

    def link_stop(self):
        global LINK_SERVICE

        if LINK_SERVICE:
            LINK_SERVICE.service_stop()

    def link_disconnect(self):
        global LINK_SERVICE

        if LINK_SERVICE:
            LINK_SERVICE.service_disconnect()


