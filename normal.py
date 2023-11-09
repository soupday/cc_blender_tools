import bpy
from mathutils import Vector
from . import nodeutils, utils, vars
from .properties import CC3CharacterCache, CC3MaterialCache

def normal_to_height(normal_image: bpy.types.Image, height_image: bpy.types.Image, iterations = 10):

    pixels = pixels = list(normal_image.pixels)
    w = int(normal_image.size[0])
    h = int(normal_image.size[1])
    l = w*h

    N: Vector
    D: Vector
    T: Vector

    # convert to normal vectors
    normals = [None]*l
    for i in range(0, l):
        p = i*4
        x = 2*pixels[p]-1
        y = 2*pixels[p+1]-1
        z = 2*pixels[p+2]-1
        N = Vector((x,y,z))
        #N.normalize()
        normals[i] = N

    directional_displacements = []

    print("Building directional displacements")
    for j in range(-1, 2):
        for k in range(-1, 2):
            D = Vector((j, -k, 0))

            if k == 0 and j == 0:
                directional_displacements.append(None)

            else:
                displacement_map = [0]*l
                for i in range(0, l):
                    N = normals[i]
                    a = N.dot(D)
                    T = D - N*a
                    T.normalize()
                    d = T.z * 0.5 * D.length
                    displacement_map[i] = d
                directional_displacements.append(displacement_map)

    heights = [0]*l
    for itx in range(0, iterations):
        print(f"iteration: {itx}")
        for v in range(0, h):
            for u in range(0, w):
                i = u+v*w
                height = 0
                for j in range(-1, 2, 1):
                    uu = min(max(u+j, 0), w-1)
                    for k in range(-1, 2, 1):
                        if j == 0 and k == 0: continue
                        vv = min(max(v+k, 0), h-1)
                        ii = uu + vv*w
                        jk = j + 3*k + 4
                        d = directional_displacements[jk][ii] + directional_displacements[jk][i]
                        height += heights[ii] - d
                height /= 8
                heights[i] = height

    min_height = 999999
    max_height = -999999
    abs_height = 0
    for i in range(0, l):
        min_height = min(min_height, heights[i])
        max_height = max(max_height, heights[i])
        abs_height = max(abs_height, abs(heights[i]))

    print(f"min: {min_height} max: {max_height} abs: {abs_height}")

    pixels = list(height_image.pixels)
    for i in range(0, l):
        p = i * 4
        h = min(5*0.5*heights[i]/abs_height + 0.5,1)
        pixels[p] = h
        pixels[p+1] = h
        pixels[p+2] = h
    height_image.pixels[:] = pixels


def build_displacement_system(chr_cache: CC3CharacterCache, mat_cache: CC3MaterialCache):

    mat: bpy.types.Material = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    normal_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(NORMAL)")
    normal1_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(WRINKLENORMAL1)")
    normal2_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(WRINKLENORMAL2)")
    normal3_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(WRINKLENORMAL3)")
    blend_normal_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(NORMALBLEND)")


    image = bpy.data.images["3K1L562.png"]
    if "TEST_HEIGHT" in bpy.data.images:
        height_image = bpy.data.images["TEST_HEIGHT"]
        height_image.scale(image.size[0], image.size[1])
    else:
        height_image = bpy.data.images.new("TEST_HEIGHT", image.size[0], image.size[1], is_data=True)

    height_image.pixels[0] = 0

    normal_to_height(image, height_image, 5)

    return














