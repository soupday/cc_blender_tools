import bpy

def find_pose_bone(*name):
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        obj = p.object
        if (obj.type == "ARMATURE"):
            for n in name:
                if n in obj.pose.bones:
                    return obj.pose.bones[n]
    return None