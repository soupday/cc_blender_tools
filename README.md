# CC3 Blender Tools
Add-on for importing and auto setup of Character Creator 3 character exports.

## Installation, Updating, Removal
### To Install
- Download the latest release [0.1-alpha](https://github.com/soupday/cc3_blender_tools/archive/0_1_alpha.zip).
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
## Usage
This add-on is meant to be used on a single CC3 Character at a time. As such it is not meant to be used as part of a complex scene but rather to prepare characters for rendering or to edit character morphs or accessories.

The add-on consists of three main panels:
### CC3 Import
#### Import Character
The import character button will import a .fbx or .obj export from CC3. The add-on will invoke the correct importer with the nescessary settings depending on which type of file is selected. The animation option can be unchecked to import the character without any pose or animation data.
Some notes on what to export from CC3:
- All **FBX** (To Blender) and **OBJ** character exports can be used for rendering or general use, but the **OBJ**->**Nude Character in Bind Pose** export does not export any materials.
- FBX export options should set **Target Tool Preset** to Blender.
- OBJ export options should check the **Export Materials** box (if available).
- To create _character morphs_ the export must generate an .fbxkey or .objkey file:
    * For **OBJ** exports, only the **OBJ**->**Nude Character in Bind Pose** will generate an .objkey file.
    * For **FBX** exports, the **FBX Options** parameter should be set to **Mesh Only** to generate an .fbxkey file,
    * _or_
    * the **FBX Options** parameter should be set to **Mesh and Motion** with the **Include Motion** parameter set to **Callibration**
#### Build Materials
Here you can set the material parameters used to construct the materials for the character.
- **Basic Materials** - The materials will be built as standard PBR materials utilising the base diffuse, ambient occlusion, specular, metallic, roughness, alpha and normal or bump maps where available.
- **Advanced Materials** - The materials will be build using more advanced node groups to utilise texture blending, colour/roughness/specular overlays, texture scaling, cavity AO maps, micro-normals, blend normals and subsurface scattering.
- **Alpha Blend** - When a non opaque material is detected the add-on will use standard alpha blending for this material.
- **Alpha Hashed** - When a non opaque material is detected the add-on will use alpha hashing for the this material. Alpha hashing solves many z-sorting problems but may require more samples to render.
- **All Imported** - When selected the add-on will build materials for all objects from the imported character.
- **Only Selected** - When selected the add-on will only build materials for the currently selected objects (and child objects of the selection)
- **Hair Hint** - The add-on does not know which object represents the hair mesh, so it tries to guess from the name of the object and materials, the object whose name contains one of these keywords will be considered the hair mesh.
- **Scalp Hint** - Likewise the scalp mesh (which should be part of the hair mesh) needs to be identified, any material in the hair object that matches one of these keywords is considered to be the scalp material.
- **Hair Object** - If the hair mesh auto detection fails, the hair object can be chosen directly with this object picker.
Finally
- **Build Materials** - Builds the materials for the character using the current build settings. Materials can be rebuild at any time.
#### Fix Alpha Blending
The buttons in this section can be used to quickly correct and alpha blend settings for clothing or accessories that where not correctly detected as opaque/non-opaque. These buttons operate on the currently selected objects.

You can choose between alpha blending or alpha hashing for blend modes. Also there are buttons to see an objects material to single or double sided.
#### Adjust Parameters
This is the real focus of the add-on. The parameters section governs all the various parameters to control how the textures and maps are used and mixed together to create the final appearance.

Each material type: Skin, eyes, hair, teeth, tongue, nails and other (default) types are all detected and setup independently with their own parameter sets. Basic materials have a much smaller subset of parameters, the advanced materials allow fine control of just about everything.

Material parameters will be adjusted in real time as the parameter sliders are changed, giving instant feedback.

- **All Imported** - When selected all objects from the imported character will have their parameters updated.
- **Selected Only** - When selected only the selected objects will have their parameters updated.
- **Update** - Force an update of all/selected parameters.

...

#### Utilities
Here are some useful utility functions.
- **Open Mouth** - The mouth can be opened to see within the mouth cavity. This operation uses a bone constraint and does overwrite any animation or pose, Set this back to zero to remove the contraint.
- **Reset Parameters** - Resets all parameters back to their defaults and updates the character materials.
- **Rebuild Node Groups** - This will delete and rebuild the node groups for the advanced materials. Materials will need to be rebuilt afterwards.
### CC3 Scene Tools
In this panel there are some functions to quickly create a few different lighting setups and render settings.
- **Solid Matcap** - Solid viewport shading with matcap and cavity shading.
- **Blender Default** - Material shading with a single point light and the forest HDRi, the default blender setup.
- **CC3 Default** - Material shading with a 3 point lighting setup roughly the same as the CC3 application default character lighting.
- **Studio Right** - Rendered shading with right sided 3 point lighting with contact shadows using the Studio HDRi.
- **Courtyard Left** - Rendered shading with left sided 3 point lighting with contact shadows using the Courtyard HDRi.
- **3 Point Tracking & Camera** - Rendered shading with tracking lights and camera, independent light and camera targets. It also sets up the world and compositor node trees ready for custom mapped HDRi in the world nodes and glare and lens distortion in the compositor.
### CC3 Pipeline


