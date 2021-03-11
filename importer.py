import math
import os

import bpy

from .cache import *
from .cleanup import *
from .groups import *
from .materials import *
from .nodes import *
from .physics import *
from .scene import *
from .utils import *
from .vars import *


def process_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps

    reset_nodes(mat)

    node_tree = mat.node_tree
    nodes = node_tree.nodes
    shader = None
    cache = get_material_cache(mat)

    if props.hair_object is None and is_hair_object(obj, mat):
        props.hair_object = obj

    # find the Principled BSDF shader node
    for n in nodes:
        if (n.type == "BSDF_PRINCIPLED"):
            shader = n
            break

    # create one if it does not exist
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")

    clear_cursor()

    if props.setup_mode == "COMPAT":
        connect_compat_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    elif is_eye_material(mat):

        if props.setup_mode == "BASIC":
            connect_basic_eye_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            connect_adv_eye_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    elif is_tearline_material(mat):

        connect_tearline_material(obj, mat, shader)

    elif is_eye_occlusion_material(mat):

        connect_eye_occlusion_material(obj, mat, shader)
        move_new_nodes(-600, 0)

    elif is_mouth_material(mat) and props.setup_mode == "ADVANCED":

        connect_adv_mouth_material(obj, mat, shader)
        move_new_nodes(-600, 0)

    else:

        if props.setup_mode == "BASIC":
            connect_basic_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            connect_advanced_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    # apply cached alpha settings
    if cache is not None:
        if cache.alpha_mode != "NONE":
            apply_alpha_override(obj, mat, cache.alpha_mode)
        if cache.culling_sides > 0:
            apply_backface_culling(obj, mat, cache.culling_sides)

def scan_for_hair_object(obj):
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if is_hair_object(obj, mat):
                return obj
    return None


def init_character_for_edit(obj):
    #bpy.context.active_object.data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    set_shape_key_edit(obj)

    if obj.type == "ARMATURE":
        for child in obj.children:
            init_character_for_edit(child)


def set_shape_key_edit(obj):
    try:
        #current_mode = bpy.context.mode
        #if current_mode != "OBJECT":
        #    bpy.ops.object.mode_set(mode="OBJECT")
        #bpy.context.view_layer.objects.active = object
        obj.active_shape_key_index = 0
        obj.show_only_shape_key = True
        obj.use_shape_key_edit_mode = True
    except:
        log_error("Unable to set shape key edit mode!")


def process_object(obj, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if obj is None or obj in objects_processed:
        return

    objects_processed.append(obj)

    log_info("Processing Object: " + obj.name + ", Type: " + obj.type)

    cache = get_object_cache(obj)

    # try to determine if this is the hair object, if not set
    if props.hair_object is None:
        props.hair_object = scan_for_hair_object(obj)

    # when rebuilding materials remove all the physics modifiers
    # they don't seem to like having their settings changed...
    remove_all_physics_mods(obj)
    # process any materials found in a mesh object
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if mat is not None:
                log_info("Processing Material: " + mat.name)
                process_material(obj, mat)
                if prefs.physics == "ENABLED" and props.physics_mode == "ON":
                    add_material_weight_map(obj, mat, create = False)

        # setup default physics
        if prefs.physics == "ENABLED" and props.physics_mode == "ON":
            add_collision_physics(obj)
            if len(get_weight_map_mods(obj)) > 0:
                enable_cloth_physics(obj)

    elif obj.type == "ARMATURE":
        # set the frame range of the scene to the active action on the armature
        if obj.animation_data is not None and obj.animation_data.action is not None:
            frame_count = math.ceil(obj.animation_data.action.frame_range[1])
            bpy.context.scene.frame_end = frame_count

    # process child objects
    for child in obj.children:
        process_object(child, objects_processed)


def get_material_dir(base_dir, character_name, import_type, obj, mat):
    if import_type == "fbx":
        object_name = strip_name(obj.name)
        mesh_name = strip_name(obj.data.name)
        material_name = strip_name(mat.name)
        if "cc_base_" in object_name.lower():
            path = os.path.join(base_dir, "textures", character_name, character_name, mesh_name, material_name)
            if os.path.exists(path):
                return path
        path = os.path.join(base_dir, "textures", character_name, object_name, mesh_name, material_name)
        if os.path.exists(path):
            return path
        return os.path.join(base_dir, character_name + ".fbm")

    elif import_type == "obj":
        return os.path.join(base_dir, character_name)


def cache_object_materials(obj):
    props = bpy.context.scene.CC3ImportProps
    main_tex_dir = props.import_main_tex_dir
    base_dir, file_name = os.path.split(props.import_file)
    type = file_name[-3:].lower()
    character_name = file_name[:-4]

    if obj is None:
        return

    if obj.type == "MESH":
        for mat in obj.data.materials:
            if mat.node_tree is not None:
                cache = props.material_cache.add()
                cache.material = mat
                cache.object = obj
                cache.dir = get_material_dir(base_dir, character_name, type, obj, mat)
                nodes = mat.node_tree.nodes
                # weight maps

                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        filepath = node.image.filepath
                        dir, name = os.path.split(filepath)
                        # detect incorrent image paths for non packed (not embedded) images and attempt to correct...
                        if node.image.packed_file is None:
                            if os.path.normcase(dir) != os.path.normcase(main_tex_dir):
                                log_warn("Import bug! Wrong image path detected: " + dir)
                                log_warn("    Attempting to correct...")
                                correct_path = os.path.join(main_tex_dir, name)
                                if os.path.exists(correct_path):
                                    log_warn("    Correct image path found: " + correct_path)
                                    node.image.filepath = correct_path
                                else:
                                    correct_path = os.path.join(cache.dir, name)
                                    if os.path.exists(correct_path):
                                        log_warn("    Correct image path found: " + correct_path)
                                        node.image.filepath = correct_path
                                    else:
                                        log_error("    Unable to find correct image!")
                        name = name.lower()
                        socket = get_input_connected_to(node, "Color")
                        # the fbx importer in 2.91 makes a total balls up of the opacity
                        # and connects the alpha output to the socket and not the color output
                        alpha_socket = get_input_connected_to(node, "Alpha")
                        if socket == "Base Color":
                            cache.diffuse = node.image
                        elif socket == "Specular":
                            cache.specular = node.image
                        elif socket == "Alpha" or alpha_socket == "Alpha":
                            cache.alpha = node.image
                            if "diffuse" in name or "albedo" in name:
                                cache.alpha_is_diffuse = True
                        elif socket == "Color":
                            if "bump" in name:
                                cache.bump = node.image
                            else:
                                cache.normal = node.image


class CC3Import(bpy.types.Operator):
    """Import CC3 Character and build materials"""
    bl_idname = "cc3.importer"
    bl_label = "Import"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Select the root directory to search for the textures.",
        subtype="FILE_PATH"
        )

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Import Animation", description = "Import animation with character.\nWarning: long animations take a very long time to import in Blender 2.83", default = True)

    running = False
    imported = False
    built = False
    lighting = False
    timer = None
    clock = 0

    def import_character(self):
        props = bpy.context.scene.CC3ImportProps

        import_anim = self.use_anim
        # don't import animation data if importing for morph/accessory
        if self.param == "IMPORT_MORPH":
            import_anim = False
        props.import_file = self.filepath
        dir, name = os.path.split(self.filepath)
        props.import_objects.clear()
        props.material_cache.clear()
        type = name[-3:].lower()
        name = name[:-4]
        props.import_type = type
        props.import_name = name
        props.import_dir = dir
        props.import_space_in_name = " " in name

        if type == "fbx":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name + ".fbm")
            if os.path.exists(props.import_main_tex_dir):
                props.import_embedded = False
            else:
                props.import_main_tex_dir = ""
                props.import_embedded = True

            # invoke the fbx importer
            tag_objects()
            bpy.ops.import_scene.fbx(filepath=self.filepath, directory=dir, use_anim=import_anim)

            # process imported objects
            imported = untagged_objects()
            for obj in imported:
                if obj.type == "ARMATURE":
                    p = props.import_objects.add()
                    p.object = obj
                elif obj.type == "MESH":
                    cache_object_materials(obj)
            log_info("Done .Fbx Import.")

        elif type == "obj":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name)
            props.import_embedded = False
            if not os.path.exists(props.import_main_tex_dir):
                props.import_main_tex_dir = ""

            # invoke the obj importer
            tag_objects()
            if self.param == "IMPORT_MORPH":
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "OFF",
                        use_split_objects = False, use_split_groups = False,
                        use_groups_as_vgroups = True)
            else:
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "ON",
                        use_split_objects = True, use_split_groups = True,
                        use_groups_as_vgroups = False)

            # process imported objects
            imported = untagged_objects()
            for obj in imported:
                # scale obj import by 1/100
                obj.scale = (0.01, 0.01, 0.01)
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    if self.param == "IMPORT_MORPH":
                        if props.import_main_tex_dir != "":
                            #reconstruct_obj_materials(obj)
                            pass
                    else:
                        cache_object_materials(obj)
            log_info("Done .Obj Import.")

    def build_materials(self):
        objects_processed = []
        props = bpy.context.scene.CC3ImportProps

        check_node_groups()

        if props.build_mode == "IMPORTED":
            for p in props.import_objects:
                if p.object is not None:
                    process_object(p.object, objects_processed)

        elif props.build_mode == "SELECTED":
            for obj in bpy.context.selected_objects:
                process_object(obj, objects_processed)

        log_info("Done Build.")

    def run_import(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # use basic materials for morph/accessory editing as it has better viewport performance
        if self.param == "IMPORT_MORPH":
            props.setup_mode = prefs.morph_mode
        elif self.param == "IMPORT_ACCESSORY":
            props.setup_mode = prefs.pipeline_mode
        # use advanced materials for quality/rendering
        elif self.param == "IMPORT_QUALITY":
            props.setup_mode = prefs.quality_mode

        self.import_character()

        # check for fbxkey
        if props.import_type == "fbx":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".fbxkey")
            props.import_haskey = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_haskey:
                message_box("This character export does not have an .fbxkey file, it cannot be used to create character morphs in CC3.", "FBXKey Warning")


        # check for objkey
        if props.import_type == "obj":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".ObjKey")
            props.import_haskey = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_haskey:
                message_box("This character export does not have an .ObjKey file, it cannot be used to create character morphs in CC3.", "OBJKey Warning")

        self.imported = True

    def run_build(self, context):
        self.build_materials()
        self.built = True

    def run_lighting(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # use the cc3 lighting for morph/accessory editing
        if self.param == "IMPORT_MORPH" or self.param == "IMPORT_ACCESSORY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                if props.import_type == "fbx":
                    setup_scene_default(prefs.pipeline_lighting)
                else:
                    setup_scene_default(prefs.morph_lighting)
            # for any objects with shape keys select basis and enable show in edit mode
            for p in props.import_objects:
                init_character_for_edit(p.object)

        # use portrait lighting for quality mode
        elif self.param == "IMPORT_QUALITY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                setup_scene_default(prefs.quality_lighting)

        zoom_to_character()
        self.lighting = True

    def modal(self, context, event):

        # 60 second timeout
        if event.type == 'TIMER':
            self.clock = self.clock + 1
            if self.clock > 60:
                self.cancel(context)
                self.report({'INFO'}, "Import operator timed out!")
                return {'CANCELLED'}

        if event.type == 'TIMER' and not self.running:
            if not self.imported:
                self.running = True
                self.run_import(context)
                self.clock = 0
                self.running = False
            elif not self.built:
                self.running = True
                self.run_build(context)
                self.clock = 0
                self.running = False
            elif not self.lighting:
                self.running = True
                self.run_lighting(context)
                self.clock = 0
                self.running = False

            if self.imported and self.built and self.lighting:
                self.cancel(context)
                self.report({'INFO'}, "All done!")
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # import character
        if "IMPORT" in self.param:
            if self.timer is None:
                self.imported = False
                self.built = False
                self.lighting = False
                self.running = False
                self.clock = 0
                self.report({'INFO'}, "Importing Character, please wait for import to finish and materials to build...")
                context.window_manager.modal_handler_add(self)
                self.timer = context.window_manager.event_timer_add(1.0, window = context.window)
                return {'PASS_THROUGH'}

        # build materials
        elif self.param == "BUILD":
            self.build_materials()

        # rebuild the node groups for advanced materials
        elif self.param == "REBUILD_NODE_GROUPS":
            rebuild_node_groups()

        elif self.param == "DELETE_CHARACTER":
            delete_character()

        return {"FINISHED"}

    def invoke(self, context, event):
        if "IMPORT" in self.param:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        return self.execute(context)

    @classmethod
    def description(cls, context, properties):
        if properties.param == "IMPORT":
            return "Import a new .fbx or .obj character exported by Character Creator 3"
        elif properties.param == "REIMPORT":
            return "Rebuild the materials from the last import with the current settings"
        elif properties.param == "IMPORT_MORPH":
            return "Import .fbx or .obj character from CC3 for morph creation. This does not import any animation data.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. For best results for morph creation export FBX: 'Mesh Only' or OBJ: Nude Character in Bind Pose, as these guarantee .fbxkey or .objkey generation.\n" \
                   "2. OBJ export 'Nude Character in Bind Pose' .obj does not export any materials.\n" \
                   "3. OBJ export 'Character with Current Pose' does not create an .objkey and cannot be used for morph creation.\n" \
                   "4. FBX export with motion in 'Current Pose' or 'Custom Motion' also does not export an .fbxkey and cannot be used for morph creation"
        elif properties.param == "IMPORT_ACCESSORY":
            return "Import .fbx or .obj character from CC3 for accessory creation. This will import current pose or animation.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. OBJ or FBX exports in 'Current Pose' are good for accessory creation as they import back into CC3 in exactly the right place"
        elif properties.param == "IMPORT_QUALITY":
            return "Import .fbx or .obj character from CC3 for rendering"
        elif properties.param == "BUILD":
            return "Build (or Rebuild) materials for the current imported character with the current build settings"
        elif properties.param == "DELETE_CHARACTER":
            return "Removes the character and any associated objects, meshes, materials, nodes, images, armature actions and shapekeys. Basically deletes everything not nailed down.\n**Do not press this if there is anything you want to keep!**"
        elif properties.param == "REBUILD_NODE_GROUPS":
            return "Rebuilds the shader node groups for the advanced and eye materials."
        return ""

