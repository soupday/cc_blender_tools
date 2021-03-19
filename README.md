# CC3 Blender Tools
An add-on for importing and automatically setting up materials for Character Creator 3 character exports.

Using Blender in the Character Creator 3 pipeline can often feel like hitting a brick wall. Spending potentially hours having to get the import settings correct and setting up the materials often with hundreds of textures.

This add-on aims to reduce that time spent getting characters into Blender down to just a few seconds and make use of as many of the exported textures as possible so that character artists can work in the highest quality possible using Blender.

### How it works
The character exports from CC3 have a very rigid naming structure. The folders the textures are stored in always follow the same pattern e.g. _filename_.obj exports exporting all textures into the _filename_ folder and .fbx exports store textures in the _filename_.fbm folder and in textures/_filename_/_objectname_/_meshname_/_materialname_ folders amongst others. All objects in the export have unique names and unique material names with all texture names following a similar convention such as _materialname_ + _type_ e.g. 'Std_Skin_Head_Diffuse.png' or 'Vest_Normal.png'. Thus textures for each material can be easily discovered without the need for deep recursive scans for texture files. The add-on then reconstructs the material nodes, for each object and material, using these textures and the material setup parameters as needed (This bit isn't so easy...).

On the way this add-on also resolves a few bugs and idiosyncrasies in Blender, namely the FBX importer attaching the wrong opacity for the eyes, hair and eyelashes and a curious bug in the importers for both OBJ and FBX where Blender can't find the right textures if the exported file has spaces in the name and there is more than one character in the same folder. It has something to do with 3DS Max replacing all spaces with underscores when it exports and uses spaces as a separator for multiple texures, so the Blender coders made their importers work the same way...

For this reason:
**Warning: when exporting characters to and from Blender - DO NOT put spaces in the file name.**

## Installation, Updating, Removal
### To Install
- Download the latest release [0.2.2](https://github.com/soupday/cc3_blender_tools/archive/0_2_2.zip).
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
- All **FBX** (To Blender) and **OBJ** character exports can be used for rendering or general use, but the **File**->**Export**->**OBJ**->**Nude Character in Bind Pose** menu export does not export any materials.
- FBX export (**File**->**Export**->**FBX (Clothed Character)** menu) options should set **Target Tool Preset** to **Blender**.
- OBJ export (**File**->**Export**->**OBJ**->**Character with Current Pose** menu) options should check the **Export Materials** box.
- To create _character morphs_ the export must generate an .fbxkey or .objkey file:
    * For **OBJ** exports, only the **File**->**Export**->**OBJ**->**Nude Character in Bind Pose** menu exporter will generate an .objkey file.
    * For **FBX** exports use **File**->**Export**->**FBX (Clothed Character)** menu where the **FBX Options** parameter should be set to **Mesh Only** to generate an .fbxkey file,
    * _or_
    * the **FBX Options** parameter should be set to **Mesh and Motion** with the **Include Motion** parameter set to **Calibration**
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
- **Open Mouth** - The mouth can be opened to see within the mouth cavity. This operation uses a bone constraint and does not overwrite any animation or pose, Set this back to zero to remove the contraint.
- **Reset Parameters** - Resets all parameters back to their defaults and updates the character materials.
- **Rebuild Node Groups** - This will delete and rebuild the node groups for the advanced materials. Materials will need to be rebuilt afterwards.
### CC3 Scene Tools
In this panel there are some functions to quickly create a few different lighting setups and render settings.
- **Solid Matcap** - Solid viewport shading with matcap and cavity shading.
- **Blender Default** - Material shading with a single point light and the forest HDRi, the default blender setup.
- **CC3 Default** - Material shading with a 3 point lighting setup roughly the same as the CC3 application default character lighting.
- **Studio Right** - Rendered shading with right sided 3 point lighting with contact shadows using the Studio HDRi.
- **Courtyard Left** - Rendered shading with left sided softer 3 point lighting with contact shadows using the Courtyard HDRi.
- **3 Point Tracking & Camera** - Rendered shading with tracking lights and camera, independent light and camera targets. It also sets up the world and compositor node trees ready for custom mapped HDRi in the world nodes and glare and lens distortion in the compositor.
### CC3 Pipeline
The purpose of this panel is to provide quick methods of importing and exporting characters and accessories for specific purposes in order to streamline as much as possible the pipeline between CC3 and Blender. As such this panel goes first in the tool tab, but it is described last here, in order to fully understand what it does.
#### Render / Quality
- **Import Character** - Imports the character for rendering. Sets the material build mode to advanced and applies the **Studio Right** scene lighting setup.
#### Morph Editing
- **Import For Morph** - Imports the character for morph editing. Sets the material build mode to basic for better viewport performance and sets the scene lighting to **CC3 Default** (this can be changed in the preferences). If the imported character file has no corresponding .fbxkey or .objkey it will show a warning message that this character cannot be used for creating character morphs.
- **Export Character Morph** - Exports the character, with the same filetype as imported, for reimport back into CC3.
    * FBX exports should be imported back into CC3 using the **File**->**Import** menu _or_ the **Create**->**Cloth, Hair, Acc ( With FbxKey )**, these appear to do the same thing and will replace the current character with the imported one. It will ask for the **Decrypt Key File**, this is the .fbxkey generated with the original character export from CC3. It's important to note that the character is imported without any materials as the blender fbx export does not support material data, or it's in a form that CC3 does not recognize. Once imported a morph of the character can be created using the **Create**->**Head & Body Morph Sliders** menu, or an accessory can be created from any of the imported objects.
    * OBJ exports should be imported back into CC3 using the **Create**->**Morph Slider** Editor menu. Select either the Default Morph (for full body morphs) or Current Morph (for relative morphs) as the **Source Morph**, then select the .obj file exported as the **Target Morph**, with the original characters .objkey for the **Checksum File Path**
#### Accessory Editing
- **Import For Accessory** - Imports the character for accessory creation / editing. Sets the material build mode to basic for better viewport performance and sets the scene lighting to **CC3 Default** or to **Solid Matcap** if the .obj character has no materials (this can be changed in the preferences). This does not require an fbxkey or objkey if making non skin weighted accessories.
- **Export Accessory** - Exports the selected object(s) as accessories. These should be imported into CC3 using the **Create->Accessory** menu. The accessory will be imported without any materials. If the character was originally exported from CC3 in **Current Pose** the accessory export _should_ import back into CC3 in exactly the right place.
#### Settings
- **Auto Lighting** - The auto setup of the lighting can be turned off here if you don't want the add-on to mess with your lighting or render settings. It can also be turned off completely in the preferences.
#### Cleanup
- **Delete Character** - This will delete the character and any associated objects, meshes, materials, nodes, images, armature actions and shapekeys. Basically deletes everything not nailed down. **Do not press this if there is anything you want to keep!**