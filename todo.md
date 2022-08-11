# TODO

## Bugs
- Exporting nude character with bind pose does not correct for heel adjustments. Do not export for morph editing *any* character wearing shoes.

- Facial hair and eye brows must be reset/re-applied on import as they loose all their facial expression blend shapes on import.


## To Add

- Export / Bake Rigify > Unity
    - Optional export Just animation to Unity, (just those meshes with shapekey tracks?).
    - Optional export full face rig/just eyes and jaw
    - Optional export/bake(NLA) shapekey actions.

- use HIK profile to setup rig on humanoids

- use RLSSS shader for generic exports with Subsurface nodes attached?

- in CC4 plugin, check for duplicate names on *export* and warn.


- Accessories are placed as extentions to armature: try to make control rig for them?
- Remove deform status from Twist bone containers in import (UpperArm, LowerArm, etc...)
- for obj imports, the humanoid/creature/prop box shows...
- eye/cornea shader iris emmission
- PBR shader color tint
- texture matching / reduction

## To Test

bake textures, normals, flow maps
basic materials
clean up character data
convert generic to non standard
convert genertic materials to rl pbr

standard exports (all, json updates, textures remap and copy, physics weightmaps and data)
non standard exports (not converted)
exports to unity blend and fbx


imports textures, detecting materials by name, from json, tex_dirs...