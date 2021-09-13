# CC3 Blender Tools
An add-on for importing and automatically setting up materials for Character Creator 3 character exports.

Using Blender in the Character Creator 3 pipeline can often feel like hitting a brick wall. Spending potentially hours having to get the import settings correct and setting up the materials often with hundreds of textures.

This add-on aims to reduce that time spent getting characters into Blender down to just a few seconds and make use of as many of the exported textures as possible so that character artists can work in the highest quality possible using Blender.

[Online Documentation](https://soupday.github.io/cc3_blender_tools/index.html) (Work in progress...)

[Reallusion Forum Thread](https://forum.reallusion.com/475005/Blender-Auto-Setup)

## Installation, Updating, Removal
### To Install
- Download the [latest release](https://github.com/soupday/cc3_blender_tools/releases).
- In Blender go to menu **Edit**->**Preferences** then select **Add-ons**.
- Click the **Install** button at the top of the preferences window and navigate to where you downloaded the zip file, select the file and click **Install Add-on**.
- Activate the add-on by ticking the checkbox next to **Edit**->**Preferences** then select **Add-ons**
- The add-ons functionality is available through the **CC3** Tab in the tool menu to the right of the main viewport. Press _N_ to show the tools if they are hidden.
### To Remove
- From the menu: **Edit**->**Preferences** then select **Add-ons**
- In the search box search **All** add-ons for **"CC3 Tools"**
- Deactivate the add-on by unticking the checbox next to **Edit**->**Preferences** then select **Add-ons**.
- Then click the **Remove** button.
### To Update
- Remove the current version of the add-on by following the remove instructions above.
- Follow the installation instructions, above, to install the new version.

## Changelog

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

