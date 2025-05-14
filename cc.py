


import bpy
from mathutils import Matrix, Vector
from . import bones, utils, vars


def set_pose_bone_world_transform(arm, pose_bone: bpy.types.PoseBone, world_transform: dict, local_transform: dict):
    if arm and pose_bone and world_transform and local_transform:
        loc = utils.array_to_vector(world_transform["location"]) * 0.01
        rot = utils.array_to_quaternion(world_transform["rotation"])
        s = utils.array_to_vector(world_transform["scale"])
        sca = Vector((utils.sign(s.x), utils.sign(s.y), utils.sign(s.z))) * arm.scale
        M = utils.make_transform_matrix(loc, rot, sca)
        pose_bone.matrix = M


def set_mesh_world_transform(arm, mesh_obj: bpy.types.Object, world_transform: dict, local_transform: dict):
    if arm and mesh_obj and world_transform and local_transform:
        loc = utils.array_to_vector(world_transform["location"]) * 0.01
        rot = utils.array_to_quaternion(world_transform["rotation"])
        s = utils.array_to_vector(world_transform["scale"])
        sca = Vector((utils.sign(s.x), utils.sign(s.y), utils.sign(s.z))) * arm.scale
        M = utils.make_transform_matrix(loc, rot, sca)
        mesh_obj.matrix_world = M


def bone_name_match(rl_name, blender_name):
    if rl_name == "_Object_Pivot_Node_":
        rl_name = "CC_Base_Pivot"
    export_name = bones.rl_export_bone_name(rl_name)
    unduplicated_name = utils.strip_name(blender_name)
    if rl_name == unduplicated_name or export_name == unduplicated_name:
        return True
    return False


def deduplicate_name(name, names: dict):
    count = names[name] if name in names else 0
    names[name] = count + 1
    return f"{name}.{count:03d}" if count > 0 else name


def match_id_tree(rl_tree, arm=None,
                  pose_bone: bpy.types.PoseBone=None,
                  mesh_obj: bpy.types.Object=None,
                  parent_bone: bpy.types.PoseBone=None,
                  id_map=None,
                  names=None,
                  pose=False):
    """If supplying an armature, match the bone tree to the armature and return a mapping (by id)
       to the armature bones. If no armature (i.e. for rigified avatars), then map the bones (by id)
       to unduplicated bone names"""

    if arm and not (pose_bone or mesh_obj):
        pose_bone = arm.pose.bones[0]
    if id_map is None:
        id_map = {}
    if names is None:
        names = {}
    name = pose_bone.name if pose_bone else mesh_obj.name if mesh_obj else deduplicate_name(rl_tree["name"], names)
    # id_map is a dict of bones by ID, mapping the source skin_bone name to the armature bone or mesh
    id_map[rl_tree["id"]] = {
        "source": rl_tree["name"],
        "name": name,
        "mesh": mesh_obj is not None,
    }
    # id tree
    id_tree = {
        "name": name,
        "id": rl_tree["id"],
        "source": rl_tree["name"],
        "children": []
    }
    world_transform_data = rl_tree.get("world_transform", None)
    local_transform_data = rl_tree.get("local_transform", None)
    if mesh_obj:
        id_tree["mesh"] = True
        if pose and world_transform_data:
            set_mesh_world_transform(arm, mesh_obj, world_transform_data, local_transform_data)
    else:
        if pose and world_transform_data:
            set_pose_bone_world_transform(arm, pose_bone, world_transform_data, local_transform_data)
        #utils.log_detail(f"Bone: {bone.name} / Tree: {rl_tree['name']} {rl_tree['id']}")
        for child_tree in rl_tree["children"]:
            child_name = child_tree["name"]
            #utils.log_detail(f"Trying: {child_name}")
            if arm:
                found = False
                if not found and not child_tree["children"]:
                    for obj in arm.children:
                        if obj.parent and obj.parent_type == "BONE" and obj.parent_bone == pose_bone.name:
                            if bone_name_match(child_name, obj.name):
                                #utils.log_detail(f" - child_mesh: {obj.name} / child_tree: {child_name} - parented to: {obj.parent_bone}")
                                found = True
                                child_tree = match_id_tree(child_tree, arm=arm, mesh_obj=obj, parent_bone=pose_bone, id_map=id_map, pose=pose)[0]
                                if child_tree:
                                    id_tree["children"].append(child_tree)
                                break
                if not found:
                    for child_bone in pose_bone.children:
                        if bone_name_match(child_name, child_bone.name):
                            #utils.log_detail(f" - child_bone: {child_bone.name} / child_tree: {child_name}")
                            found = True
                            child_tree = match_id_tree(child_tree, arm=arm, pose_bone=child_bone, id_map=id_map, pose=pose)[0]
                            if child_tree:
                                id_tree["children"].append(child_tree)
                            break
            else:
                child_tree = match_id_tree(child_tree, id_map=id_map, names=names)[0]
                if child_tree:
                    id_tree["children"].append(child_tree)
    return id_tree, id_map


def confirm_bone_order(bones, ids, id_map: dict):
    result = True
    for id, id_def in id_map.items():
        if id not in ids or id_def["source"] not in bones:
            utils.log_warn(f"bone {id_def['source']} ({id}) not found in skin bones!")
            result = False
    if result and len(ids) < len(id_map):
        utils.log_info("All bones present, but more bones found in id_tree!")
    elif result:
        utils.log_info("All bones present!")
    return result


def convert_id_tree(arm, id_tree_root):
    if not id_tree_root: return None
    id_tree, id_map = match_id_tree(id_tree_root, arm=arm)
    return id_tree, id_map