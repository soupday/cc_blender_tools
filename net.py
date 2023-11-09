import bpy
import socket
import time
from . import utils, vars

BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333

HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 60
PING_INTERVAL_S = 10
TIMER_INTERVAL_S = 0.1

CLIENT_ONLY = True

class CCiCListener(bpy.types.Operator):
    """Socket Listener"""
    bl_idname = "ccic.listener"
    bl_label = "Listener"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    time: float = 0
    timer: bpy.types.Timer = None
    clock: float = 0
    server_sock: socket.socket = None
    client_sock: socket.socket = None
    client_ip: str = "127.0.0.1"
    client_port: int = RL_PORT
    link_client: bool = False
    link_server: bool = False
    ping_timer: float = 0
    keepalive_timer: float = 0

    def cancel(self, context):
        props = bpy.context.scene.CC3ImportProps
        props.link_stop = False
        props.link_disconnect = False
        self.stop_timer(context)
        self.stop_client()
        self.stop_server()
        self.report({'INFO'}, f"Link Stopped!")

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps

        if self.param == "START":
            if CLIENT_ONLY:
                if not props.link_connected:
                    if self.try_connect():
                        self.start_timer(context)
                        return {"RUNNING_MODAL"}
            else:
                if not props.link_connected and not props.link_listening:
                    self.start_timer(context)
                    if not self.try_connect():
                        self.start_server()
                        return {"RUNNING_MODAL"}

            return {'FINISHED'}

        if self.param == "DISCONNECT":
            if props.link_connected:
                props.link_disconnect = True
            return {'FINISHED'}

        elif self.param == "STOP":
            props.link_stop = True
            return {'FINISHED'}

        return {'FINISHED'}

    def modal(self, context, event):
        props = bpy.context.scene.CC3ImportProps

        if event.type == 'TIMER':

            current_time = time.time()
            delta_time = current_time - self.time
            self.time = current_time

            if props.link_stop:
                self.send_stop()
                self.cancel(context)
                return {'FINISHED'}

            if props.link_disconnect:
                self.send_disconnect()
                self.cancel(context)
                return {'FINISHED'}

            if props.link_connected:
                self.keepalive_timer -= delta_time
                self.ping_timer -= delta_time

                if self.ping_timer <= 0:
                    self.ping()

                if self.keepalive_timer <= 0:
                    self.cancel(context)
                    utils.log_info("lost connection!")
                    return {'FINISHED'}

            elif props.link_listening:
                self.keepalive_timer -= delta_time

                if self.keepalive_timer <= 0:
                    self.cancel(context)
                    utils.log_info("no connection within time limit!")
                    return {'FINISHED'}

            if props.link_listening and not props.link_connected:
                self.accept()

            if props.link_connected:
                message = self.recv()
                if message:
                    self.parse(message)

            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def start_server(self):
        props = bpy.context.scene.CC3ImportProps
        props.link_listening = False
        props.link_stop = False
        try:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.bind(('', BLENDER_PORT))
            self.server_sock.setblocking(0)
            self.server_sock.listen(5)
            props.link_listening = True
            self.report({'INFO'}, f"Listening on TCP *:{BLENDER_PORT}")
        except:
            self.report({'ERROR'}, f"Unable to start server on TCP *:{BLENDER_PORT}")

    def stop_server(self):
        props = bpy.context.scene.CC3ImportProps
        props.link_listening = False
        props.link_stop = False
        if self.server_sock:
            utils.log_info("Closing Server Socket")
            self.server_sock.close()
            self.link_server = False

    def stop_client(self):
        props = bpy.context.scene.CC3ImportProps
        props.link_connected = False
        props.link_stop = False
        if self.client_sock:
            utils.log_info("Closing Client Socket")
            self.client_sock.close()
            self.link_client = False

    def start_timer(self, context):
        self.time = time.time()
        if not self.timer:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
            bpy.context.window_manager.modal_handler_add(self)
            self.timer = context.window_manager.event_timer_add(TIMER_INTERVAL_S, window = bpy.context.window)
            utils.log_info("Timer started")

    def stop_timer(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            utils.log_info("Timer removed")

    def try_connect(self):
        props = bpy.context.scene.CC3ImportProps
        props.link_connected = False
        props.link_stop = False
        utils.log_info(f"attempting to connect")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((props.link_host_ip, props.link_port))
            props.link_connected = True
            self.link_client = True
            self.client_sock = sock
            self.client_ip = props.link_host_ip
            self.client_port = props.link_port
            self.keepalive_timer = KEEPALIVE_TIMEOUT_S
            self.ping_timer = PING_INTERVAL_S
            sock.setblocking(0)
            self.report({'INFO'}, f"Connected")
            utils.log_info("Connected to host")
            return True
        except:
            utils.log_info("Host not listening")
            if CLIENT_ONLY:
                self.report({'ERROR'}, f"Unable to Connect!")
            return False

    def recv(self, size=40960):
        try:
            if self.client_sock:
                message = self.client_sock.recv(size)
                return message
        except:
            pass
        return None

    def accept(self):
        props = bpy.context.scene.CC3ImportProps
        try:
            sock, address = self.server_sock.accept()
            self.client_sock = sock
            self.client_ip = address[0]
            self.client_port = address[1]
            props.link_connected = True
            self.link_server = True
            self.keepalive_timer = KEEPALIVE_TIMEOUT_S
            self.ping_timer = PING_INTERVAL_S
            utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
            self.report({'INFO'}, f"Link established: {address[0]}:{address[1]}")
        except:
            return

    def parse(self, message):
        props = bpy.context.scene.CC3ImportProps

        self.keepalive_timer = KEEPALIVE_TIMEOUT_S
        text = message.decode("utf-8")
        print(f"Message: {text}")

        if text == "STOP":
            props.link_connected = False
            props.link_stop = True
            utils.log_info(f"Link terminated by request!")

        if text == "DISCONNECT":
            props.link_connected = False
            props.link_disconnect = True
            utils.log_info(f"Link disconnected by request!")

    def send(self, message):
        props = bpy.context.scene.CC3ImportProps

        if self.client_sock and props.link_connected:
            try:
                self.client_sock.sendall(message)
            except:
                utils.log_error("Error sending message, disconnecting...")
                self.stop_client()

    def send_stop(self):
        self.send(b"STOP")

    def send_disconnect(self):
        self.send(b"DISCONNECT")

    def ping(self):
        self.ping_timer = PING_INTERVAL_S
        self.send(b"PING")
