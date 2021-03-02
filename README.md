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
- OBJ export options should check the **Export Materials** box.
- To create character morphs the export must generate an .fbxkey or .objkey file.
- For **OBJ** exports, only the **OBJ**->**Nude Character in Bind Pose** will generate an .objkey file.
- For **FBX** exports, the **FBX Options** parameter should be set to **Mesh Only** to generate an .fbxkey file,

_or_

- to **Mesh and Motion** with the **Include Motion** parameter set to **Callibration**
### CC3 Scene Tools

### CC3 Pipeline


