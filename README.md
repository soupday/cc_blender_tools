# CC/iC Blender Tools (Installed in Blender)
An add-on for importing and automatically setting up materials for Character Creator 3 & 4 and iClone 7 & 8 character exports.

Using Blender in the Character Creator pipeline can often feel like hitting a brick wall. Spending potentially hours having to get the import settings correct and setting up the materials often with hundreds of textures.

This add-on aims to reduce that time spent getting characters into Blender down to just a few seconds and make use of as many of the exported textures as possible so that character artists can work in the highest quality possible using Blender.

[Online Documentation](https://soupday.github.io/cc_blender_tools/index.html)

[Reallusion Forum Thread](https://forum.reallusion.com/475005/Blender-Auto-Setup)

Links
=====
[CC4 Blender Pipeline Tool (Installed in CC4)](https://github.com/soupday/CCiC-Blender-Pipeline-Plugin)

[CC3 Blender Pipeline Tool (Installed in CC3)](https://github.com/soupday/CC3-Blender-Tools-Plugin)

## Installation, Updating, Removal
### To Install
- Download the [latest release](https://github.com/soupday/cc_blender_tools/releases).
- In Blender go to menu **Edit**->**Preferences** then select **Add-ons**.
- Click the **Install** button at the top of the preferences window and navigate to where you downloaded the zip file, select the file and click **Install Add-on**.
- Activate the add-on by ticking the checkbox next to **Edit**->**Preferences** then select **Add-ons**
- The add-ons functionality is available through the **CC/iC Blender Tools** Tab in the tool menu to the right of the main viewport. Press _N_ to show the tools if they are hidden.
### To Remove
- From the menu: **Edit**->**Preferences** then select **Add-ons**
- In the search box search **All** add-ons for **"CC/iC Blender Tools"**
- Deactivate the add-on by unticking the checkbox next to **Edit**->**Preferences** then select **Add-ons**.
- Then click the **Remove** button.
### To Update
- Remove the current version of the add-on by following the remove instructions above.
- Follow the installation instructions, above, to install the new version.

## Changelog

### 2.2.4
- Rigify face rig fallback to envelope weights if auto weights fail.
- DataLink Import motion will optionally (confirmation dialog) import motion to active character if no matching character.
- Rigify head turn expression driver corrected.
- Fixed collision objects being included in export.
- Fixed displacement strength export.

### 2.2.3
- Wrinkle map region strength controls added.
- Nose crease wrinkle maps added to Mouth_Smile_* expressions.
- Export Bake:
    - Fixes and alpha fixes in Blender 4.3
    - Iris Brightness adjustments removed when baking.

### 2.2.2
- Teeth and tongue added to bone / expression drivers.
- Meta-rig bone alignment options added the Basic rig panel.
- DataLink pose functions no longer break expression drivers.

### 2.2.1
- Material and Lighting fixes for Blender 4.3.
- When exporting or sending Rigified animations: IK stretch is now disabled in the rig.
    - This should help with limb alignment problems on other platforms.
- Rigify Metarig bone rolls are aligned exactly to the CC/iC source bones now.
    - This can be disabled in the preferences (or advanced settings) to use the original Metarig bone roll alignments.
- DataLink Send Avatar will ask to overwrite (or cancel transfer) any existing *same* character.
- Generic import option to disable auto-conversion of materials.
- Fix to import hanging when no characters in FBX.
- Rebuild drivers also rebuilds Rigify shape key drivers.
- DataLink transfer Sequence and Pose actions separately labelled "Sequence" and "Pose" no longer just "DataLink" for both.
- Operations that use object or mesh duplicates no longer duplicate the actions on the objects.


### 2.2.0
- Character Management functions - CCiC Create > Character Management:
    - Transfer weights supports split body meshes.
    - Voxel head diffuse skinning (if installed) button for selected character meshes.
    - Clean Empty Data: Removes empty shape keys and empty vertex groups from the character meshes.
    - Blend Body Weights: Blends body vertex weights with existing vertex weights on selected objects based on distance from the surface of the body, to correct vertex weighting for clothing items that don't conform correctly to the body, e.g. from Voxel Heat Diffusion weights or from Daz original weights.
- New scene presets added:
    - scene view transform and world background strength controls added.

### 2.1.10
- Sets up Rigidbody physics when _appending_ a character from another library blend file via the Append button in the import panel.
    - Note: Rigidbody physics does *not* work with linked character _overrides_.
- Export non-standard character fix.
- Support for split meshes when exporting, rebuilding materials, physics & rigging:
    - Any mesh separated or duplicated from a source character mesh will be considered part of the character and an extension of that object.
    - For split body meshes, the mesh with the head will be used as the source for facial expression drivers and wrinkle map drivers.
    - Note: Split *body* meshes will _not_ import back into CC4 as standard CC3+ characters.
- Added buttons to rebuild and to remove just the expression and bone drivers to the Character Build Settings panel.

### 2.1.9
- Maintain operator context for scene operations.
- Align to view distance fix.

### 2.1.8
- Fixes to view 3d shading context in 4.2.
- Imported objects, materials, images and actions detection no longer uses tags.
- Added more checks to skip null material slots.

### 2.1.7
- Sync lights includes Scene IBL from CC/iC visual settings.
- Export to CC3/4 button fixed.
- Added extra checks for AccuRig / ActorScan when unknown humanoids detected.

### 2.1.6
- Import supports multiple file selection.
    - To import multiple objects from a folder, press shift + select the FBX files in the importer file selection window.
- Fixes for blender version before 4.0:
    - Replace mesh OBJ export.
    - Rigging bone layer assignment.
    - Property collection clear.
    - Rigging widget control scale.

### 2.1.5
- Proportion edit should work on all character types (except Rigified)
- Sync lights and send pose should work in all modes and keeps the active mode.
- Lighting brightness adjust slider.
- Some GameBase detection fixes.
- GameBase skin roughness tweaks.
- Fix for vertex color sampling when json data is missing.


### 2.1.4
- DataLink receive Update / Replace function, to replace whole characters or selected parts.
- Fix to character validation and clean-up.

### 2.1.3
- Motion Set UI errors fixed.
- Eevee-Next SSR Eyes fixes.
- Iris brightness render settings for Eevee & Cycles.
- Bake fixes for Blender 4.2 refractive eyes.
- Export-Bake warnings when not build for Eevee.
- Lighting tweaks.

### 2.1.2
- Blender 4.2 lighting settings fixes and adjustments.
    - Eevee-Next Raytracing, shadows and shadow jitter enabled on render settings and lights.
    - Blender 4.0+ lighting presets use AgX.
- Eevee & Cycles global material options.
    - Control of SSS weights, roughnes power and normals for various material types.

### 2.1.1
- Fix UDIM flattening on proportion editing and sculpt base mesh transfer.
- Lighting sync area correction.
- DataLink plugin version compatibility check.

### 2.1.0
- Motion Sets:
    - Action name remapping and retargetting overhaul.
    - Motion set functions: Load/Push/Clear/Select/Rename/Delete
    - Motion prefix and use fake user option added for all animation retargeting and import.
    - Motion set filter and motion set info function.
- NLA Tools:
    - NLA Bake functions moved to NLA editor panel.
    - Motion set panel in rigging and NLA editor and DataLink.
    - NLA strip alignment and sizing utility functions.
- Fixes:
    - Duplicating character no longer duplicates actions.
    - Store object state checks objects/materials exist.
    - Positioning fixes with rigify

### 2.0.9
- DataLink:
    - DataLink main loop stability improvements.
    - Live sequence back to CC4/iClone takes facial expression bone rotations into account.
    - Live Sequence stop button.
    - Replace mesh function: Quickly send (non topology changing) mesh alterations back to CC4.
    - Update material & texture function: Send selected material data and textures back to CC4.
    - Sync lighting recalculations.
- Export:
    - Restores armature and object states after export.
    - Fix to baking custom Diffuse Map channel.
- Fix to Blender 3.4-3.6 Eevee subsurface color.
- Material Parameter controls disabled for linked characters (unless library override).


### 2.0.8
- Import/Export:
    - Fix to Update Unity Project being greyed out after saving as Blend file.
    - Fix to export non-standard character.
    - Fix to export non-standard ARP rigged character.
    - (Blender 4.0+) Fix to reverting object and material name changes on export and other force name changes.
    - Generic character/prop import expanded to support USD/USDZ.
    - Rigify export now have choice of naming system:
        - Metarig names (without Root bone) for exporting animations back into CC/iC.
        - CC Base names (with Root bone) for exporting to Unity Auto-setup.
    - Rigified characters/motion exports now generate custom HIK profile which can be used to import/convert Rigified motion exports into CC/iC.
    - DataLink Rigified characters (optionally) disable tweak bones as they are not compatible with CC/iC animation.
- Scene tools:
    - Scene lighting presets overhauled.
    - Added function to align any object to view location and orientation (useful for placing lights and cameras).
    - Added function to add a camera at current view location and orientation.
    - Added function to setup a main face tracking camera centered on character's head.
    - Added function to convert current view studio lighting into world lighting node setup.
- Rigify:
    - Fix to GameBase detection.
    - Fix to AccuRig generation code not being recognized as valid Rigify target.
    - Fix to support Mixamorigs with suffix numbers in retargeting.
    - Auto-retarget toggle added to automatically retarget any animation on character when using Quick Rigify.
- Shaders:
    - Skin, eye and hair shaders updated to use Blender 4.0+ Random Walk (Skin) Subsurface Scattering.
    - Displacement map (if present) will be used on skin materials for bump and mesh displacement.
    - Cycles subsurface calculations and parameters tweaked.
    - Separate cycles modifiers for Blender 3.4-3.6 and 4.0+.
    - Eye Sclera color tint added.
    - Cycles Tearline shader reworked.
- Character Management
    - Character edit function added.
    - Character duplicate function added (duplicates character objects and meta-data so can be used and configured independently).
    - Character tools (select/rigify/convert/delete/duplicate), also sub-panel in DataLink.
    - Convert to accessory fix.
- DataLink:
    - Added Receiving prop posing and animation live sequence.
    - Added custom prop rig control bones when sending through datalink.
    - Added Direct Motion Transfer from CC/iC (automatic motion export->import).
    - Added "Go iC" button to send (just props for now) back to iClone.

### 2.0.7
- Attempts to restore datalink when reloading linked blend file.
- All returning datalink operators will attempt to first reconnect if not connected.
- Facial expressions included in datalink send pose and sequence. (But not visemes)
    - Currently certain expression bone movements are conflicting with existing bone movements.
    - You may wish to avoid the Head_Turn expressions as a consequence.
- Character Proportion editing mode added to CC/iC Create panels.
- Spring bone hair binding will add an armature modifier for the hair object if absent, to allow binding for newly created hair mashes.
- Scale body weights now acts on the normalized existing hair weights.

### 2.0.6
- Restored Rigify retarget limb correction utilities.
- Fix to Blender 4.1 import crash caused by 4.1 removing auto-smoothed normals.

### 2.0.5
- Fix to converting generic objects to props.
- Fix to baking value textures back to CC4 when exporting converted props and humanoids.
- DataLink data send rate synchronization improvements.
- Rigify retarget and NLA bake options to bake to FK/IK/Both.
    - Rig FK/IK mode set appropriately, unchanged when baking to 'Both'.
- Quick FK/IK switch button added to rigify mini-panel.
- Send Rigified pose or sequence fix.
- Rigify Jaw alignment changed to -Z.

### 2.0.4
- Linking/Appending:
    - Added linking/append functions to auto-link to characters in blend files with full character data and functionality.
    - Added connect function to re-build character data for linked/appended characters.
    - Added custom properties to armatures/meshes and materials to aid re-connection of character data.
    - Rebuilding materials will add this custom data to existing characters.
    - Auto-linked/Re-connected characters can use full add-on functionality i.e. rigging, retargeting, exporting, rebuilding materials, etc...
- Rigify:
    - DataLink pose retargeting teeth position fix.
    - Eye bone and jaw bone alignments corrected.
    - Face rig jaw constraints adjusted for less lip deformation.
- Parallax eye shader AO fix.
- Basic materials SSS fixes.
- Importing a bad or incompatible mesh should fail more gracefully.

### 2.0.3
- DataLink:
    - Lighting and Camera sync.
    - Send Character (Go-CC) back to CC4.
    - Facial expressions and Visemes transferred in the pose and animation sequencing.
    - Animation sequence now writes to rig and shape-key action tracks directly using low level fast keyframing, all at once at the end. Which is much faster, for both native rig and Rigify rig.
    - Sequence rate matching so CC4 doesn't get too far ahead of itself.
    - Supports Morph editing and mesh updating for sending back morph OBJ for automatic morph slider creation in CC4.
- Subsurface Recalculations (you may need to reset the preferences in the add-on prefs)
- Export of Hue, Sat, Brightness params to CC4.
- Fixed SSS material detection.
- Fixed ActorBuild generation detection and export.
- HIK and facial profiles copied with character export (if generated by CC4)
- OBJ import/export fix for Blender 4.0.
- OBJ import now supports full materials.
- Fixed T-pose orientation when exporting Rigified animation.

### 2.0.2
- Correction to malformed json texture paths when exporting character from CC4 directly to the root of a drive.
- Disabled image search on FBX importer, should import a little faster now.

### 2.0.1
- VRM import fixes.
    - VRM to CC4 export generates HIK profile for auto characterization.
- Rigify fixes:
    - Face bone roll axis corrections.
    - Tongue bone meta-rig positioning corrections.
    - Teeth bone retargeting corrections.

### 2.0.0
- Blender 4.0 support.
- WIP Experimental DataLink added:
    - Currently in alpha stages, more a proof of concept at the moment.
- Bake add-on updated and merged into this project.

### 1.6.1
- Object Management:
    - Generic material conversion better detects AO maps in Blender 3+
    - Transfer vertex weights with posed armature fix.
    - Empty transform hierarchy to Prop conversion puts bones in the right correct places.
- Exporting rigified animations with parented armatures now excludes those armatures from export.

### 1.6.0.4
- Fixed bake rigify retarget not assigning action to rig after baking
- Removes facial expression bone drivers on Rigifying (caused cyclic dependencies)
- Re-importing/rebuilding materials on a character will reload any texture images that are being re-used from existing or previous imports, just in case they have been changed on disk.
    - Except when the image has been modified by the user and has not yet been saved.
- NLA Bake fix.
- Fix Generic character import.
- Spring rig panels show if character is invalid for spring rigging.
- Expression drivers for bones only apply to CC4 Ext and Std profiles
- Bone drivers for direct visemes Ah and Oh added.
- Viseme bone drivers now excluded when Jaw drivers are disabled.
- Export Rigified motion and Unity T-Pose generation fix.


### 1.6.0
- Rigifying character keeps meta-rig and allows for Re-Rigifying the control rig from the meta-rig.
    - Useful for re-aligning bones, re-positioning face rig, etc...
- First draft of (optional) Dual Specular skin shader (Eevee & Cycles) with specular micro details.
- Added build options to generate drivers for Jaw, Eyes and Head bones from facial expression shape keys.
- Added build option to generate drivers for all expression shape keys driven from the body mesh shape keys.
    - Which means only the expressions on the body mesh need to be updated/animated.
- Fix to turn off vertex colours in hair materials when hair mesh has blank vertex colour data (i.e. all zero).
- Facial Expression shape key value range expanded to -1.5 - 1.5 (except for eye look shape keys)
- Characters exported with Mouth Open as Morph, now correctly detects the body mesh.
- Fix to support sphere colliders in collisions shapes.
- Some additional lighting arrangements: Authority and Blur Warm.

### 1.5.8.5
- Fixes:
    - Fix to empty transforms or deleted objects in export.
    - Fix to transfer vertex weights leaving working copies behind.
    - Some object management UI corrections.
    - Fix to bake path when exporting character converted from generic with materials added after conversion.
    - Fix to replace selected bones from hair cards.
    - Fix cloth settings error in detect physics.
    - Fix CC4 spring bones creation.
    - Fix to exports of objects which originally had duplicate object names.
    - Fix to import collider parenting crash when using Blender versions before 3.5
    - Fix to UI panel in 2.93.
    - Fix to collider generation in 2.93
    - Fix to collider generation when Rigifying when posed.

### 1.5.8
- Spring Bones:
    - Blender spring bone rigid body simulation added for spring bone hair rigs.
    - Spring bone simulation controls.
    - Hair spring bone chain renaming.
    - Bone generation truncate and smoothing parameters.
    - Added support for not quad grid poly mesh hair cards, should work with any hair mesh.
    - Rigid body colliders for the spring bones that use the collision shapes from character creator.
    - Rigify update for spring bone system.
    - FK, IK and tweak bones for spring rigs.
    - Rigify and spring bone UI updates.
    - Baking spring bone simulation and animation into new animations
    - Exporting rigified spring bone characters and animations, including the rigid body simulation as animation.
- Cloth Physics overhaul:
    - Physics UI update.
    - Better mapping of PhysX weight map to blender vertex pin weights.
    - Physics presets updates, mass, tension and bending to better simulate the cloth type and work more consistently with external forces.
    - Cloth physics preset detection on import.
    - UI tools for point cache baking.
    - Fixes to weightmap paint mode resetting texture.
    - Browse button for painted weightmap, so you can find it.
    - Weightmap assignment fix for materials with the same base name.
- Sculpt / Mesh:
    - Character geometry transfer to shape-keys function.
- Character Objects:
    - Add object to character (from another character) now copies the object into the new character.
    - Transfer weight maps now works when posed to effectively parent in place target mesh.
- Other:
    - Fix to eye close slider.

### 1.5.7
- Hair bone de-duplication.
- Bones from grease pencil lines or hair card generation now replaces (matching) existing bones.
- Grease Pencil lines generated only from active grease pencil layer, allowing for better organization.
- Added some color space fallbacks when using different color space configurations.

### 1.5.6
- Relative wrinkle strengths for individual wrinkle maps implemented.
- Overall wrinkle strength and curve power slider added the head material parameters.
- Competing wrinkle maps now use additive blending to solve overlap.
- Brow correction added for brow raise + brow compress wrinkles.
- Generated images not yet saves are autosaved for export (so they get included).
- Add custom bone function for hair rigging.

### 1.5.5
- Flow maps added to wrinkle map system.
- Better texture limiting for the head material.
- Fix to export crash when a texture field is missing in the JSON data.
- Corrupted JSON data detection and error report on import/build.
    - In some cases resetting the collision shapes in CC4 will fix corrupted JSON data.

### 1.5.4
- Wrinkle Map system implemented.
    - Characters with wrinkle maps will setup wrinkle shaders in the head material automatically.
    - Preferences for Build Wrinkle Maps.
- OpenColorIO ACES color space support.
    - Preferences for ACES color space overrides.
- Optional Texture Packing and Texture limits added to reduce number of textures in imported materals.
    - Some systems can have very low texture limits (i.e. only 8 on some OSX systems) this can help import full CC4 characters.
    - Preferences for pack and/or limit textures.
- Body sculpting updated:
    - All sculpting modes work on a copy of the character.
    - Multi-res applied base shape copied back to original character in a way that preserves existing shape keys.
    - AO Map added to baking, layers and export.
    - Additional strength, definition and mix mode controls added to layer ui.
- Spring Bone Hair Rigging (Cloth Rigging to follow)
    - Added initial Hair curve extraction from hair cards.
    - Spring bone hair generation from selected hair cards or greased pencil lines on surface.
    - Hair card weight binding fine tuning controls.
    - Hair cards are weighted individualy to neighboring bones and uniformly across to avoid lateral stretch and behaves more like cloth physics implementations.
    - Spring bone generation from grease pencil lines.
- Fixes:
    - Some extra transparency material detection.
    - Fix to hand & finger bone roll alignment when bind pose has arms and hands at a steep downward angle.
    - Fix to partial material name matching errors from ActorCore and AccuRig.
    - Export bake socket fix for Blender 3.4+.
    - Shapekey locks will be disabled and all shapekeys reset to zero on character export.

### 1.5.3
- Fix to retarget baking in Blender 3.4 not baking pose bones to rigify armature action.
- Fix to Rigify motion export bone root name.

### 1.5.2
- Rigify IK-FK influence controls replicated in Rigging panel.
- Fix to material setup error caused by missing normal map data.

### 1.5.1
- Fix to Generic character export.
- Fix to Generic converted character export.

### 1.5.0
- Rigify export mesh and/or animation overhaul.
- Smoothing groups added to export file dialog options.
- Support for CC4 Plugin, facial expression and viseme data export.
- Fix to legacy hair detection & scalp detection.
- Very slight subsurface added to scalp to prevent the dark/blueish artifacts on skin.
- Fix to bump maps connecting to normal sockets.
- Eye limbus darkness recalculated.
- Initial attempt at exporting Blender 3.3 Curve hair on characters via Alembic export.

### 1.4.9
- Fix to embedded image correction and image filepath comparisons.
- Fix to basic material texture loading.
- Convert to Accessory function added to Object Management.

### 1.4.8
- Adding existing RL material to a new character import will copy the material data.

### 1.4.7
- Match existing materials (for AccuRig imports) button added to Create tab and Rigify info pane.
    - Attempts to assign existing materials to the AccuRig import that match the original export to AccurRig.
    - For a Blender > AccuRig / ActorCore > Blender round trip workflow.
- Eye occlusion (Eevee) color darkened.
- Hair shader (Eevee) Specular blend added (Base surface Specularity -> Anisotropic Specularity)

### 1.4.6
- Fix for palm control location with less than 5 fingers.

### 1.4.5
- Fix for ActorCore / AccuRig import detection.

### 1.4.4
- Missing bone chains from CC3 rig will hide corresponding control rig bones (e.g. missing fingers)
- Export texture baking no longer duplicates baking on same materials across different objects.
- Export fix to CC3/4 when material name starts with a digit.
- Fix to import/convert of multiple generic GLTF/GLB props or characters.
- Fix to exporting Roughness and Metallic texture strength (should always be 100).

### 1.4.3
- Export bake maps now correctly sets bit depth and no alpha channel. Opacity texture bakes should work now.
- Convert generic character from objects to props added.
- Auto converts generic imports where possible, when using the import character button.
- Texture and material de-duplication (optional)
- ActorCore rigify accessory fix.
- CC/iC Create tab and panels added.
    - Physics & Object Management moved to CC/iC Create.
    - Multi-res sculpt & bake helper tools panels added.

### 1.4.2
- Separate Iris & Sclera emission colors for parallax eye shader.
- Displacement calculation reworked as it behaves differently in Blender 3.2.1 (was causing triangulation artifacts)

### 1.4.1
- Fixes
    - Export T-pose action created correctly when character bind pose is already a T-pose.
    - Tongue subsurface scatter parameter fixes in UI.
    - Hair material UI corrected in Blender 3.2.1 (caused by renamed icon enums)
- Accessory bones now copy to rigify rig.

### 1.4.0
- Physics JSON changes and additions export.
- Unity T-pose export fix.
- Body Collision Mesh fix.
- Unity export logic fixes.
- Resize weightmap function.
- Increment/decrement paint strenth weightmap buttons.
- Image path writeback fix.

### 1.3.9
- Full Json data generation added.
- Rigify Toe IK Stretch Fix for Blender 3.1+
- Convert to Non-standard function.
- Convert from Generic character to Reallusion material based non-standard character.
- Export baking fixes and default PBR export support added.

### 1.3.8
- UI naming update.
- Repository rename to **cc_blender_tools** (title **CC/iC Blender Tools**), old repo links still apply.
- Initial support for exporting _any_ non-standard characters to CC4.
    - Character should be aligned -Y forward, Z up for correct bone translation in CC4.
    - Json data constructed on export to try and reconstruct materials using the **CC4 Blender Tools Plugin**.
        - Materials must be based on Principled BSDF otherwise only texture name matching is possible.
    - non-standard characters rigged with Auto-Rig Pro will (try to) invoke the ARP export operator (if installed)
        - ARP export operator cleans up the rig and leaves only the relevent deformation bones.
    - Import functions expanded to allow import from FBX, GLTF and VRM for non-standard characters.
        - These are **not** considered to be CC/iC characters and have no material parameter, rigging or physics options.

### 1.3.7
- Iris Color and Iris Cloudy Color added.
- Tool bar tab renamed from **CC3** to **CC/iC**
- Some UI button name changes.

### 1.3.6
- Rigify
    - Finger roll alignment fixed. All fingers now have exactly the same local bend axis.
    - Disables all physics modifiers non-contributing armatures and meshes during retarget baking to speed it up a bit.
- Physics:
    - Low poly (1/8th) Collision Body mesh created from decimating a copy of the Body mesh and removing the eyelashes.
        - Hair would easily get trapped in the eyelashes and a lower poly collision mesh should speed up the cloth simulation.
    - PhysX weight maps normalized, provides a more consistent and controllable simulation across different weight maps.
    - Tweaked some cloth simulation parameters.
    - Smart Hair meshes in particular should simulate better now.
- Unity:
    - Added animation export options (Actions or Strips)

### 1.3.5
- Fix to shape-key action name matching.

### 1.3.4
- Rigify Retargeting:
    - GameBase animation retargeting to CC Rigified Rig.
    - (Experimental) Mixamo animation retargeting to CC Rigified Rig.
    - Facial Expression Shape-key animation retargeting from source animation to CC character.
    - Shape-key NLA baking added (optional).
- Materials:
    - Diffuse Color, Hue, Saturation & Brightness parameters for Skin and Hair materials.
- Exporting:
    - **Export to CC3** button renamed to **Export Morph Target** when editing OBJ imports with ObjKey.
    - When **Export** button is disabled: The reason is displayed under the button.
        - Export button Key check is overridable in the add-on preferences.
- Other Changes:
    - Fix to ActorCore character (ActorCore website download) animation retargeting.
    - Basic face rig generated from full face rig and has the same jaw & eye controls and parameters.
    - Jaw pivot retargeting fixes.
    - Palm bones no longer affect deformation or generate vertex weights.
    - Crash fixes importing characters with very short names.

### 1.3.3
- CC/iC/ActorCore animation retargeting to CC Rigified Rig.
    - Preview and Bake functions for retargeted animations.
    - Arms, Legs, Heel & Height adjustments.
    - Source armature and action selector, filtering by Armature name.
- Animation importer, import multiple animations in one go.
    - Renames actions and armatures to match file names.
    - Optionally removes meshes & materials.
- Bake control rig & retargeted animations to Unity.
- Export Rigified character to Unity.
- Basic face rig drivers for __Eye Look__ blend shapes. (If character has ExPlus blend shapes)
- GameBase to Rigify support.

### 1.3.2
- Face rig Automatic Weight failure detection and (some) auto-correction.
- Support for Voxel Heat Diffuse Skinning add-on for voxel weight mapping of the face rig.

### 1.3.1
- Optional two stage Rigify process to allow modifications to the meta-rig.
- Optional basic face rigging.
- Support for ActorCore character Rigging. (Only with basic face rigging)
- Support for G3 character generation, which includes Toon base characters. (i.e. the old CC3 base)
- Support for rigging G3Plus, G3, ActorCore characters exported from iClone. (iClone exports with no bone name prefix)
- Some Control Widget fixes and scaling.
- Better character Generation check on import for exports without JSON data.

### 1.3.0
- Rigify function added.
    - Character objects are bound to the Rigify control rig.
    - Vertex weights are remapped to Rigify deformation bones.

### 1.2.2
- Object Management panel
    - All round-trip/Export object management functions moved to this panel.
    - Including checks and clean up.
    - Normalize weights function added.
- Bake/Combine Bump maps into Normal maps function added to Material Parameters panel.
- Highlight shift added to Eevee hair shader.

### 1.2.1
- Some fixes to exporting additional objects with character.
- Added a 'Check Export' function to identify potential problems with the export.

### 1.2.0
- Added initial export to Unity project function.
- Round-trip/Unity export additions and fixes.
    - Added baking raw metallic and roughness values into textures, when no textures connected, when exporting.
    - Modifiers removed from eye parts when exporting that prevented exporting blend shapes.
    - Modifiers applied on FBX exports.
    - Armature set to Pose mode on export, otherwise skeleton/bind-pose imports to CC3 incorrectly.
    - Some file path fixes when baking new textures with exports.
- Fixed skin micro-smoothness calculation causing smoothness seams between head and body materials.
- Fixed UI updating wrong unmasked micro smoothness parameter.
- Blender 3.0+ subsurface scattering method set to Christensen-Burley, rather than Random-Walk, which does not work well with hair transparencies.
- Color mixers for actor core/color masked materials prevented from generating negative/zero color values which could affect diffuse lighting.

### 1.1.9
- Fixed PBR eye material crash.

### 1.1.8
- Texture Channel Mixer added, primarily for alteration of Actor Core characters with RGB and Color ID masks, but can be used with all CC3 based materials.
- Cycles hair anisotropy reworked.
- Cycles parameter tweaks:
    - Brighter iris settings for SSR eyes.
    - Hair subsurface reduced (May want to turn it off completely, there can be too many artifacts generated in the hair.)
    - Skin subsurface slightly increased.

### 1.1.7
- Cornea material detection crash fix.

### 1.1.6
- Baking add-on compatibility update.

### 1.1.5
- Character and Object operators (**Character Settings** Panel):
    - Add object to character, with parenting and armature modifier.
    - Convert and add materials to character to use with material parameters and export write back.
    - Transfer body vertex weights to object.
    - Clean up object and material character data.
    - Export back to CC3 will include Texture & Json data for any new objects added with these operators.
- Fix to Subsurface scattering for Blender 3.0 Cycles renders.
- Cycles adjustment settings added to preferences for user fine tuning of subsurface material parameters for Cycles.

### 1.1.4
- Added more support for exporting from characters with embedded textures.

### 1.1.3
- Baking fix for Blender versions 2.83 - 2.91
- (Experimental) Added operators to add new objects to the character data.
    - See Character Settings panel with new object selected.

### 1.1.2
- Export accessory button no longer locked to character.
- Some import/export folder logic changed to try and cope with project folder & files being moved.
- Added custom texture node baking on export to CC3, including baking bump maps into normal maps on export.
    - If nodes are used to modify (or replace) texture inputs to material shaders, those nodes can be baked into the texture channel on export. This assumes the mesh has a valid UV map.
    - Bump maps can be baked into normal channels. Typically CC3 will only allow Normal maps OR bump maps for a material, not both, so an option has been added to combine them into just the normal map.

### 1.1.1
- Fix to crash from multiple character imports from iClone.
    - Note: Exporting multiple characters in one Fbx from iClone to Blender is not fully supported.
    - Characters should be exported individually.
    - If multiple characters are detected then a warning pop-up will be displayed.

### 1.1.0
- Updated export function to generate compatible Fbx file for CC3 re-import with FbxKey and to write back json material parameter and texture information. To be used in tandem with [Blender Importer Plugin for CC3 3.44](https://github.com/soupday/CC3-Blender-Tools-Plugin) for full round-trip character editing in Blender.
- Import/Export Interface simplified.
    - If character has Fbxkey then character is setup for editing. (i.e. Shapekeys locked to basis)
    - Otherwise (character is posed or has animation) character is setup for rendering.
    - Only Fbxkey character can be exported back to CC3.
- Optional Json and Texture write back for exports.
- Optional teeth rotation fix that affects some older generated characters when importing back into CC3.
- Bake on export function added to bake custom material nodes connected to master shader's texture map sockets into textures to include when re-importing back into CC3.
- Additional objects can be selected for exporting with the character, but must be properly parented and weighted with an armature modifier. Otherwise CC3 will ignore them.
- Some property and parameter fixes.

### 1.0.3
- First attempt at a single material parallax eye shader added. Which does not use SSR or transparency and thus can receive full shadows and subsurface scattering in Eevee.

### 1.0.2
- Fixed Eevee subsurface scattering settings:
    - Reworked shaders to allow for direct application of subsurface radius to Principled BSDF nodes.
    - Only the default values in the subsurface radius socket are used in Eevee rendering.
    - As such, Eevee does not support inputs to subsurface radius and so shader and parameter code needed to be re-written to accomodate this.
    - Cycles unaffected by this.
- Fixed node group upgrade code that incorrectly renamed existing node groups and did not properly replace old shader/node groups with new ones in existing blend files.

### 1.0.1
- Added render target preferences setting for Cycles and Eevee.
- Added cycles specific shaders for hair, tear-line and eye occlusion.

### 1.0.0
- Moved all shaders over to new shader model.
- Streamlined parameter and shader code to be data driven, rather than hard coded.
- Character, Object and Material parameters now stored independently for each character import.
- Json data parser to automatically set up all shader parameters.

### 0.7.4
- New eye shader model.

### 0.7.3
- New teeth and tongue shader model.

### 0.7.2
- New skin and head shader model.

### 0.7.1
- Back ported the more advanced Eye Occlusion shader from the Unity HDRP setup.
- Added displacement modifiers & parameters to Eye Occlusion and Tearline objects.
- Initial support for ActorCore models type C/D/D+.

### 0.6.3
- Fixed 'Export as accessory' correctly exporting as .obj when character was imported from an .obj file.
  (And not exporting as .fbx with the wrong file extension)

### 0.6.2
- Lighting setups set Cycles transparent bounces set to 50 to accomodate Smart Hair mesh density.
- Lighting setups do not delete existing lights or camera, but they will hide them.
- Material setup now properly detects Game Base objects (i.e. Converted to Game Base in CC3 before exporting to Blender).
- Each material now maintains it's own set of parameters.
    - Updating material parameters in **linked** mode will change the same parameters on all materials of the same type.
    - Updating parameters in **selected** only mode will only change the parameter for that one material.

### 0.5.2
- Applies IOR shader input setting when building materials.
- Exposed some build preferences in the Build Settings panel.
- Enabled SSR and refraction when importing with refractive eyes.
- Auto updater now targets Main branch for current build.

### 0.5.1
- Fixed problem appending duplicate displacment map images.
- Fixed not removing eye displacement modifiers on rebuild.
- Added eye occlusion hardness parameter.

### 0.5.0
- Refractive Eyes:
    - Iris refractive transmission with depth control and pupil size parameters.
    - Limbus parameters.
    - IOR and refractive depth parameters.
    - Blood vessel and iris bump normals.
    - Option in preferences to generate old eyes instead.
- Skin roughness power parameter added.

### 0.4.3
- Corrected an issue where the opacity maps were ignored in favour of diffuse alpha channels.
- Added opacity parameters for hair, scalp and eyelashes.
- Added roughness and specular parameters for eyelashes.
- Fixed a crash calling the import operator from from script.
- Added auto update scripts.

### 0.4.1
- Full smart hair support.
- Hair and scalp hints expanded to cover the smart hair system and moved to the preferences.
- Parameter changes update only that parameter in the imported or selected objects materials.
- Fake anisotropic highlights add to smart hair shader. (Can disable in the preferences.)
- Fake bump normals can be generated from the diffuse map if there is no normal or bump map present. (Can disable in the preferences.)
- Animation ranges only changed if physics enabled.
- Build settings and material parameters separated into their own interface panels.
- Build settings now applicable by material and the object and material build types as detected by the add-on are exposed and editable so you can fix them if it gets them wrong.
- Material parameters are context sensitive to the currently active object and material.
- Material parameters grouped into sections.
- Detects smart hair material or normal hair material and only shows relevant parameters.
- Option in preferences to gamma correct smart hair colours so they behave more like the colours in CC3.

### 0.3.0
- Fix to hair mesh detection with new smart hair system.

### 0.2.2 Alpha
- When no texture maps are present for an advanced node group, does not generate the node group.
- When exporting morph characters with .fbxkey or .objkey files, the key file is copied along with the export.
- Function added to reset preferences to default values.
- Alpha blend settings and back face culling settings can be applied to materials in the object now.
- Option to apply alpha blend settings to whole object(s) or just active materal.
- Remembers the applied alpha blend settings and re-applies when rebuilding materials.
- Option to pick Scalp Material.
- Only scans once on import for hair object and scalp material, so it can be cleared if it gets it wrong and wont keep putting it back.
- FBX import keeps track of the objects as well as the armature in case the armature is replaced.
- Physics support added:
    - Uses the physX weight maps to auto-generate vertex pin weights for cloth/hair physics (Optional)
    - Automatically sets up cloth/hair physics modifiers (Optional)
    - Physics cloth presets can be applied to the selected object(s) and are remembered with rebuilding materials.
    - Weightmaps can be added/removed to the individual materials of the objects.
    - Weight map painting added.
    - Saving of modified weight maps and Deleting weight map functions added.

