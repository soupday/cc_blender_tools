import bpy, bpy_extras
from enum import IntEnum
import os, socket, time, select, struct, json
from mathutils import Vector, Quaternion, Matrix
from . import rigging, bones, utils, vars


BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 60
PING_INTERVAL_S = 10
TIMER_INTERVAL = 1/30
MAX_CHUNK_SIZE = 32768
SERVER_ONLY = False
CLIENT_ONLY = True
CHARACTER_TEMPLATE: list = None
MAX_RECEIVE = 24


class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    NOTIFY = 50
    CHARACTER = 100
    RIGIFY = 110
    TEMPLATE = 200
    POSE = 201
    SEQUENCE = 202
    SEQUENCE_FRAME = 203
    SEQUENCE_END = 204


class LinkActor():
    name: str = "Name"
    chr_cache = None
    link_id: str = "1234567890"
    template: list = []

    def __init__(self, chr_cache):
        self.name = chr_cache.character_name
        self.link_id = chr_cache.link_id
        self.chr_cache = chr_cache
        return

    def get_chr_cache(self):
        props = bpy.context.scene.CC3ImportProps
        if not self.chr_cache:
            self.chr_cache = props.get_link_character_cache(self.link_id)
        return self.chr_cache

    def set_template(self, template):
        self.template = template


class LinkData():
    link_host: str = "localhost"
    link_host_ip: str = "127.0.0.1"
    link_target: str = "BLENDER"
    link_port: int = 9333
    actors: list = []
    # Sequence Props
    sequence_current_frame: int = 0
    sequence_start_frame: int = 0
    sequence_end_frame: int = 0
    sequence_actors: list = None

    def __init__(self):
        return

    def get_actor(self, link_id) -> LinkActor:
        props = bpy.context.scene.CC3ImportProps
        for actor in self.actors:
            if actor.link_id == link_id:
                return actor
        chr_cache = props.get_link_character_cache(link_id)
        if chr_cache:
            return self.add_actor(chr_cache)
        return None

    def add_actor(self, chr_cache) -> LinkActor:
        for actor in self.actors:
            if actor.chr_cache == chr_cache:
                return actor
        actor = LinkActor(chr_cache)
        self.actors.append(actor)
        return actor


LINK_DATA = LinkData()


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


def get_link_data_path():
    local_path = utils.local_path()
    blend_file_name = utils.blend_file_name()
    data_path = ""
    if local_path and blend_file_name:
        data_path = os.path.join(local_path, "Data Link", blend_file_name)
    return data_path


def make_datalink_import_rig(chr_cache, character_template):
    """Creates or re-uses and existing datalink pose rig for the character.
       This uses a pre-generated character template (list of bones in the character)
       sent from CC/iC to avoid encoding the bone names into the pose data stream."""

    if utils.object_exists_is_armature(chr_cache.rig_datalink_rig):
        return chr_cache.rig_datalink_rig

    no_constraints = True if chr_cache.rigified else False

    rig_name = f"{chr_cache.character_name}_Link_Rig"

    # get character armature and rigified bone mappings
    chr_rig: bpy.types.Object = chr_cache.get_armature()

    # create pose armature
    datalink_rig = utils.get_armature(rig_name)
    if not datalink_rig:
        datalink_rig = utils.create_reuse_armature(rig_name)
        edit_bone: bpy.types.EditBone
        arm: bpy.types.Armature = datalink_rig.data
        if utils.edit_mode_to(datalink_rig):
            for sk_bone_name in character_template:
                edit_bone = arm.edit_bones.new(sk_bone_name)
                edit_bone.head = Vector((0,0,0))
                edit_bone.tail = Vector((0,1,0))
                edit_bone.align_roll(Vector((0,0,1)))
                edit_bone.length = 0.1

        utils.object_mode_to(datalink_rig)

        # constraint character armature
        if not no_constraints:
            for sk_bone_name in character_template:
                chr_bone_name = bones.find_target_bone_name(chr_rig, sk_bone_name)
                if chr_bone_name:
                    bones.add_copy_location_constraint(datalink_rig, chr_rig, sk_bone_name, chr_bone_name)
                    bones.add_copy_rotation_constraint(datalink_rig, chr_rig, sk_bone_name, chr_bone_name)
                else:
                    utils.log_warn(f"Could not find bone: {sk_bone_name} in character rig!")
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


def remove_datalink_import_rig(chr_cache):
    chr_rig = chr_cache.get_armature()

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


#fcurve.keyframe_points.insert

def reset_action(chr_cache):
    if chr_cache:
        rig = chr_cache.get_armature()
        if rig:
            action = utils.safe_get_action(rig)
            action.fcurves.clear()


def prep_rig(chr_cache):
    """Prepares the character rig for keyframing poses from the pose data stream."""

    if chr_cache:
        rig = chr_cache.get_armature()
        if rig:
            action_name = f"{chr_cache.character_name}_data_link_action"
            if action_name in bpy.data.actions:
                action = bpy.data.actions[action_name]
            else:
                action = bpy.data.actions.new(action_name)
            action.fcurves.clear()
            utils.safe_set_action(rig, action)

    if chr_cache.rigified:
        BAKE_BONE_GROUPS = ["FK", "IK", "Special", "Root"] #not Tweak and Extra
        BAKE_BONE_COLLECTIONS = ["Face", "Torso", "Fingers (Detail)",
                                 "Arm.L (IK)", "Arm.L (FK)", "Leg.L (IK)", "Leg.L (FK)",
                                 "Arm.R (IK)", "Arm.R (FK)", "Leg.R (IK)", "Leg.R (FK)",
                                 "Root"]
        BAKE_BONE_LAYERS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,28]
        if utils.object_mode_to(rig):
            bone : bpy.types.Bone
            bones.make_bones_visible(rig, collections=BAKE_BONE_COLLECTIONS, layers=BAKE_BONE_LAYERS)
            for bone in rig.data.bones:
                bone.select = False
                if bones.is_bone_in_collections(rig, bone, BAKE_BONE_COLLECTIONS,
                                                           BAKE_BONE_GROUPS):
                    bone.select = True
    else:
        if utils.object_mode_to(rig):
            bone : bpy.types.Bone
            for bone in rig.data.bones:
                bone.hide = False
                bone.hide_select = False
                bone.select = True


def set_frame_range(start, end):
    bpy.data.scenes["Scene"].frame_start = start
    bpy.data.scenes["Scene"].frame_end = end


def set_frame(frame):
    bpy.data.scenes["Scene"].frame_current = frame


def key_frame_pose_visual():
    area = [a for a in bpy.context.screen.areas if a.type=="VIEW_3D"][0]
    with bpy.context.temp_override(area=area):
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_VisualLocRot')


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

    def start_server(self):
        if not self.server_sock:
            try:
                self.keepalive_timer = HANDSHAKE_TIMEOUT_S
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.bind(('', BLENDER_PORT))
                self.server_sock.listen(5)
                self.server_sockets = [self.server_sock]
                self.is_listening = True
                utils.log_info(f"Listening on TCP *:{BLENDER_PORT}")
                self.listening.emit()
                self.changed.emit()
            except:
                self.server_sock = None
                self.server_sockets = []
                self.is_listening = True
                utils.log_error(f"Unable to start server on TCP *:{BLENDER_PORT}")

    def stop_server(self):
        if self.server_sock:
            utils.log_info(f"Closing Server Socket")
            self.server_sock.close()
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
        if not self.client_sock:
            utils.log_info(f"Attempting to connect")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                self.is_connected = False
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
                self.is_connecting = False
                utils.log_info(f"Host not listening...")
                return False
        else:
            utils.log_info(f"Client already connected!")
            return True

    def send_hello(self):
        self.local_app = "Blender"
        self.local_version = bpy.app.version_string
        self.local_path = get_link_data_path()
        json_data = {
            "Application": self.local_app,
            "Version": self.local_version,
            "Path": self.local_path
        }
        self.send(OpCodes.HELLO, encode_from_json(json_data))

    def stop_client(self):
        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            self.client_sock.close()
        self.is_connected = False
        self.is_connecting = False
        self.client_sock = None
        self.client_sockets = []
        if self.listening:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
        self.client_stopped.emit()
        self.changed.emit()

    def recv(self):
        self.is_data = False
        max_receive_count = 24
        if self.client_sock and (self.is_connected or self.is_connecting):
            r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
            count = 0
            while r:
                op_code = None
                header = self.client_sock.recv(8)
                if header and len(header) == 8:
                    op_code, size = struct.unpack("!II", header)
                    data = None
                    if size > 0:
                        data = bytearray()
                        while size > 0:
                            chunk_size = min(size, MAX_CHUNK_SIZE)
                            chunk = self.client_sock.recv(chunk_size)
                            data.extend(chunk)
                            size -= len(chunk)
                    self.parse(op_code, data)
                    self.received.emit(op_code, data)
                    count += 1
                self.is_data = False
                r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                if r:
                    self.is_data = True
                    if count >= MAX_RECEIVE or op_code == OpCodes.NOTIFY:
                        return

    def accept(self):
        if self.server_sock and self.is_listening:
            r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)
            while r:
                sock, address = self.server_sock.accept()
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = address[0]
                self.client_port = address[1]
                self.is_connected = False
                self.is_connecting = True
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
                self.send_hello()
                self.accepted.emit(self.client_ip, self.client_port)
                self.changed.emit()
                r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)

    def parse(self, op_code, data):
        self.keepalive_timer = KEEPALIVE_TIMEOUT_S
        if op_code == OpCodes.HELLO:
            utils.log_info(f"Hello Received")
            self.service_initialize()
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                utils.log_info(f"Connected to: {self.remote_app} {self.remote_version}")
                utils.log_info(f"Using file path: {self.remote_path}")
        if op_code == OpCodes.PING:
            utils.log_info(f"Ping Received")
            pass
        elif op_code == OpCodes.STOP:
            utils.log_info(f"Termination Received")
            self.service_stop()
        elif op_code == OpCodes.DISCONNECT:
            utils.log_info(f"Disconnection Received")
            self.service_disconnect()

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
        if self.is_connecting:
            self.is_connecting = False
            self.is_connected = True
            self.connected.emit()
            self.changed.emit()

    def service_disconnect(self):
        self.send(OpCodes.DISCONNECT)
        self.stop_client()

    def service_stop(self):
        self.send(OpCodes.STOP)
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def loop(self):
        current_time = time.time()
        delta_time = current_time - self.time
        self.time = current_time

        if not self.timer:
            return None

        if self.is_connected:
            self.ping_timer -= delta_time
            self.keepalive_timer -= delta_time

            if self.ping_timer <= 0:
                self.send(OpCodes.PING)

            if self.keepalive_timer <= 0:
                utils.log_info("lost connection!")
                self.service_stop()
                return None

        elif self.is_listening:
            self.keepalive_timer -= delta_time

            if self.keepalive_timer <= 0:
                utils.log_info("no connection within time limit!")
                self.service_stop()
                return None

        # accept incoming connections
        self.accept()

        # receive client data
        self.recv()

        # run anything in sequence
        self.sequence.emit()

        return 0.0 if (self.is_data or self.is_sequence) else TIMER_INTERVAL

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
            except:
                utils.log_error("Error sending message, disconnecting...")
                self.lost_connection.emit()
                self.stop_client()

    def start_sequence(self, func=None):
        self.is_sequence = True
        if func:
            self.sequence.connect(func)
        else:
            self.sequence.disconnect()

    def stop_sequence(self):
        self.is_sequence = False
        self.sequence.disconnect()






LINK_SERVICE: LinkService = None

def get_link_service():
    global LINK_SERVICE
    return LINK_SERVICE


def link_state_update():
    global LINK_SERVICE
    link_data = bpy.context.scene.CCICLinkData
    link_data.link_listening = LINK_SERVICE.is_listening
    link_data.link_connected = LINK_SERVICE.is_connected
    link_data.link_connecting = LINK_SERVICE.is_connecting
    utils.update_ui()


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

        if self.param == "START":
            self.link_start()

        elif self.param == "DISCONNECT":
            self.link_disconnect()

        elif self.param == "STOP":
            self.link_stop()

        elif self.param == "SEND_POSE":
            self.send_pose()

        elif self.param == "SEND_ANIM":
            self.send_sequence()

        return {'FINISHED'}

    def prep_local_files(self):
        data_path = get_link_data_path()
        if data_path:
            os.makedirs(data_path, exist_ok=True)

    def update_link_status(self, text):
        link_data = bpy.context.scene.CCICLinkData
        link_data.link_status = text
        utils.update_ui()

    def link_start(self):
        link_data = bpy.context.scene.CCICLinkData
        global LINK_SERVICE

        self.prep_local_files()
        if not LINK_SERVICE:
            LINK_SERVICE = LinkService()
            LINK_SERVICE.changed.connect(link_state_update)
            LINK_SERVICE.received.connect(self.parse)
            LINK_SERVICE.connected.connect(self.on_connected)
        LINK_SERVICE.service_start(link_data.link_host_ip, link_data.link_port)

    def link_stop(self):
        global LINK_SERVICE

        if LINK_SERVICE:
            LINK_SERVICE.service_stop()

    def link_disconnect(self):
        global LINK_SERVICE
        if LINK_SERVICE:
            LINK_SERVICE.service_disconnect()

    SQC: int = 0

    def parse(self, op_code, data):
        global LINK_SERVICE

        if op_code == OpCodes.NOTIFY:
            self.receive_notify(data)

        if op_code == OpCodes.TEMPLATE:
            self.receive_character_template(data)

        if op_code == OpCodes.POSE:
            self.receive_pose(data)

        if op_code == OpCodes.CHARACTER:
            self.receive_character_import(data)

        if op_code == OpCodes.RIGIFY:
            self.receive_rigify_request(data)

        if op_code == OpCodes.SEQUENCE:
            self.receive_sequence(data)

        if op_code == OpCodes.SEQUENCE_FRAME:
            self.receive_sequence_frame(data)

        if op_code == OpCodes.SEQUENCE_END:
            self.receive_sequence_end(data)

        return

    def on_connected(self):
        self.send_notify("Connected")

    def send_notify(self, message):
        global LINK_SERVICE
        notify_json = { "message": message }
        LINK_SERVICE.send(OpCodes.NOTIFY, encode_from_json(notify_json))

    def receive_notify(self, data):
        notify_json = decode_to_json(data)
        self.update_link_status(notify_json["message"])

    def get_remote_export_path(self, name):
        global LINK_SERVICE
        remote_path = LINK_SERVICE.remote_path
        local_path = LINK_SERVICE.local_path
        if remote_path:
            export_folder = remote_path
        else:
            export_folder = local_path
        return os.path.join(export_folder, name)

    def get_selected_actors(self):
        global LINK_DATA
        props = bpy.context.scene.CC3ImportProps

        selected_objects = bpy.context.selected_objects
        actors = []
        for obj in selected_objects:
            chr_cache = props.get_character_cache(obj, None)
            if chr_cache:
                link_id = chr_cache.link_id
                actor = LINK_DATA.get_actor(link_id)
                if actor and actor not in actors:
                    actors.append(actor)
        return actors

    def send_actor(self):
        # TODO send_actor
        return


    def encode_character_templates(self, actors: list):
        pose_bone: bpy.types.PoseBone
        actor_data = []
        character_template = {
            "count": len(actors),
            "actors": actor_data
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
                if utils.object_mode_to(export_rig):
                    for pose_bone in export_rig.pose.bones:
                        if pose_bone.name != "root" and not pose_bone.name.startswith("DEF-"):
                            bones.append(pose_bone.name)
            else:
                # get all the bones
                rig: bpy.types.Object = chr_cache.get_armature()
                if utils.object_mode_to(rig):
                    for pose_bone in rig.pose.bones:
                        bones.append(pose_bone.name)

            actor_data.append({
                "name": chr_cache.character_name,
                "link_id": chr_cache.link_id,
                "bones": bones
            })

        return encode_from_json(character_template)

    def encode_pose_data(self, actors: list):
        pose_bone: bpy.types.PoseBone
        data = bytearray()
        data += struct.pack("!II", len(actors), bpy.context.scene.frame_current)
        actor: LinkActor
        for actor in actors:
            data += pack_string(actor.name)
            data += pack_string(actor.link_id)
            chr_cache = actor.get_chr_cache()
            if chr_cache.rigified:
                # add the import retarget rig
                if utils.object_exists_is_armature(chr_cache.rig_export_rig):
                    export_rig = chr_cache.rig_export_rig
                else:
                    export_rig = rigging.adv_export_pair_rigs(chr_cache, link_target=True)[0]
                # pack all the bone data for the exportable deformation bones
                M: Matrix = export_rig.matrix_world
                if utils.object_mode_to(export_rig):
                    for pose_bone in export_rig.pose.bones:
                        if pose_bone.name != "root" and not pose_bone.name.startswith("DEF-"):
                            T: Matrix = M @ pose_bone.matrix
                            t = T.to_translation() * 100
                            r = T.to_quaternion()
                            s = T.to_scale()
                            data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
            else:
                # pack all the bone data
                rig: bpy.types.Object = chr_cache.get_armature()
                M: Matrix = rig.matrix_world
                if utils.object_mode_to(rig):
                    pose_bone: bpy.types.PoseBone
                    for pose_bone in rig.pose.bones:
                        T: Matrix = M @ pose_bone.matrix
                        t = T.to_translation()
                        r = T.to_quaternion()
                        s = T.to_scale()
                        data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
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
                "link_id": actor.link_id,
            })
        return encode_from_json(data)

    def send_pose(self):
        global LINK_SERVICE
        mode_selection = utils.store_mode_selection_state()
        self.update_link_status(f"Sending Current Pose Set")
        self.send_notify(f"Pose Set")
        # get actors
        actors = self.get_selected_actors()
        # send template data first
        template_data = self.encode_character_templates(actors)
        LINK_SERVICE.send(OpCodes.TEMPLATE, template_data)
        # send pose data
        pose_data = self.encode_pose_data(actors)
        LINK_SERVICE.send(OpCodes.POSE, pose_data)
        utils.restore_mode_selection_state(mode_selection)

    def send_animation(self):
        return

    def send_sequence(self):
        global LINK_SERVICE
        global LINK_DATA

        self.update_link_status(f"Sending Animation Sequence")
        self.send_notify(f"Animation Sequence")
        # get actors
        actors = self.get_selected_actors()
        # reset animation to start
        bpy.context.scene.frame_current = bpy.context.scene.frame_start
        LINK_DATA.sequence_current_frame = bpy.context.scene.frame_current
        # send animation meta data
        sequence_data = self.encode_sequence_data(actors)
        LINK_SERVICE.send(OpCodes.SEQUENCE, sequence_data)
        # send template data first
        template_data = self.encode_character_templates(actors)
        LINK_SERVICE.send(OpCodes.TEMPLATE, template_data)
        # start the sending sequence
        LINK_DATA.sequence_actors = actors
        LINK_SERVICE.start_sequence(self.send_sequence_frame)

    def send_sequence_frame(self):
        global LINK_SERVICE
        global LINK_DATA

        # set/fetch the current frame in the sequence
        current_frame = ensure_current_frame(LINK_DATA.sequence_current_frame)
        self.update_link_status(f"Sequence Frame: {current_frame}")
        # send current sequence frame pose
        pose_data = self.encode_pose_data(LINK_DATA.sequence_actors)
        LINK_SERVICE.send(OpCodes.SEQUENCE_FRAME, pose_data)
        # check for end
        if current_frame >= bpy.context.scene.frame_end:
            LINK_DATA.sequence_actors = None
            LINK_SERVICE.stop_sequence()
            self.send_sequence_end()
            return
        # advance to next frame now
        LINK_DATA.sequence_current_frame = next_frame(current_frame)

    def send_sequence_end(self):
        LINK_SERVICE.send(OpCodes.SEQUENCE_END)

    def decode_character_templates(self, template_data):
        global LINK_DATA

        template_json = decode_to_json(template_data)
        count = template_json["count"]
        for actor_data in template_json["actors"]:
            link_id = actor_data["link_id"]
            name = actor_data["name"]
            actor = LINK_DATA.get_actor(link_id)
            if actor:
                actor.set_template(actor_data["bones"])
            else:
                utils.log_error(f"Unable to find actor: {name} ({link_id})")
        return template_json

    def decode_pose_data(self, pose_data):
        global LINK_DATA
        count, frame = struct.unpack_from("!II", pose_data)
        ensure_current_frame(frame)
        LINK_DATA.sequence_current_frame = frame
        offset = 8
        actors = []
        for i in range(0, count):
            offset, name = unpack_string(pose_data, offset)
            offset, link_id = unpack_string(pose_data, offset)
            actor = LINK_DATA.get_actor(link_id)
            if not actor:
                utils.log_error(f"Unable to find actor: {name} ({link_id})")
            if actor:
                actors.append(actor)
                datalink_rig = make_datalink_import_rig(actor.chr_cache, actor.template)
            # unpack the binary transform data directly into the datalink rig pose bones
            for bone_name in actor.template:
                tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
                offset += 40
                if actor:
                    pose_bone: bpy.types.PoseBone = datalink_rig.pose.bones[bone_name]
                    loc = Vector((tx, ty, tz)) * 0.01
                    rot = Quaternion((rw, rx, ry, rz))
                    sca = Vector((sx, sy, sz))
                    pose_bone.rotation_mode = "QUATERNION"
                    pose_bone.rotation_quaternion = rot
                    pose_bone.location = loc
                    pose_bone.scale = sca

        return actors

    def receive_character_template(self, data):
        self.decode_character_templates(data)
        self.update_link_status(f"Character Templates Received")

    def select_actor_rigs(self, actors, prep=False):
        rigs = []
        for actor in actors:
            rig = actor.chr_cache.get_armature()
            if rig:
                if prep:
                    prep_rig(actor.chr_cache)
                rigs.append(rig)
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

    def receive_pose(self, data):
        self.update_link_status(f"Pose Data Receveived")
        actors = self.decode_pose_data(data)
        self.select_actor_rigs(actors, prep=True)
        key_frame_pose_visual()
        for actor in actors:
            remove_datalink_import_rig(actor.chr_cache)
        set_frame(bpy.context.scene.frame_current)

    def receive_sequence(self, data):
        global LINK_SERVICE
        global LINK_DATA

        self.update_link_status(f"Receiving Live Sequence...")
        json_data = decode_to_json(data)
        # sequence frame range
        LINK_DATA.sequence_start_frame = json_data["start_frame"]
        LINK_DATA.sequence_end_frame = json_data["end_frame"]
        # sequence actors
        actors_data = json_data["actors"]
        actors = []
        for actor_data in actors_data:
            name = actor_data["name"]
            link_id = actor_data["link_id"]
            actor = LINK_DATA.get_actor(link_id)
            if actor:
                prep_rig(actor.chr_cache)
                actors.append(actor)
        LINK_DATA.sequence_actors = actors
        # set the range
        set_frame_range(LINK_DATA.sequence_start_frame, LINK_DATA.sequence_end_frame)
        set_frame(LINK_DATA.sequence_start_frame)
        # start the sequence
        LINK_SERVICE.start_sequence()

    def receive_sequence_frame(self, data):
        global LINK_SERVICE
        global LINK_DATA

        actors = self.decode_pose_data(data)
        self.update_link_status(f"Sequence Frame: {LINK_DATA.sequence_current_frame}")
        self.select_actor_rigs(actors, prep=False)
        key_frame_pose_visual()

    def receive_sequence_end(self, data):
        global LINK_SERVICE
        global LINK_DATA

        num_frames = LINK_DATA.sequence_end_frame - LINK_DATA.sequence_start_frame
        actor: LinkActor
        for actor in LINK_DATA.sequence_actors:
            remove_datalink_import_rig(actor.chr_cache)
        LINK_SERVICE.stop_sequence()
        LINK_DATA.sequence_actors = None
        self.update_link_status(f"Live Sequence Complete: {num_frames} frames")
        bpy.context.scene.frame_current = LINK_DATA.sequence_start_frame
        bpy.ops.screen.animation_play()

    def receive_character_import(self,data):
        global LINK_DATA

        json_data = decode_to_json(data)
        fbx_path = json_data["path"]
        name = json_data["name"]
        link_id = json_data["link_id"]
        actor = LINK_DATA.get_actor(link_id)
        if actor:
            self.update_link_status(f"Character: {name} exists!")
            utils.log_error(f"Actor {name} ({link_id}) already exists!")
            return
        self.update_link_status(f"Receving Character Import: {name}")
        if os.path.exists(fbx_path):
            bpy.ops.cc3.importer(param="IMPORT", filepath=fbx_path)
            actor = LINK_DATA.get_actor(link_id)
            self.update_link_status(f"Character Imported: {actor.name}")

    def receive_rigify_request(self, data):
        global LINK_SERVICE

        json_data = decode_to_json(data)
        name = json_data["name"]
        link_id = json_data["link_id"]
        actor = LINK_DATA.get_actor(link_id)
        if actor:
            self.update_link_status(f"Rigifying: {actor.name}")
            actor.chr_cache.select()
            bpy.ops.cc3.rigifier(param="ALL", no_face_rig=True)
            self.update_link_status(f"Character Rigified: {actor.name}")

