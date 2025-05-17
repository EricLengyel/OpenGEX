# OpenGEX Blender Importer

This contains an Import plugin for OpenGEX files. 

Uses python 3. Tested with Blender 3.3.

## Importer Features

This importer is incomplete. It only imports static meshes with materials, as well as lights and cameras.

It also comes with an OpenGex python parser, which is separate from Blender plugin itself, based on Eric's Lengyel C++ importer example and a very (very) barebones math library.

## Limitations

The importer does not support animations and other related data structures (yet).

## Blender debugging setup

- Download VS Code;
- Install python 3, specific version will depend on Blender's python version;
- Install VS Code pythons extension. Go to View -> Extensions, search for python;
- Download https://github.com/AlansCodeLog/blender-debugger-for-vscode ;
- Create a folder to put the unzip debugger plugin. Should be <path_to_chosen_folder>/addons/<plugin_folder>, copy the unzipped folder;
- In Blender, go to Edit -> Preferences -> Addons and search for Debugger for VS Code and enable it;
- Enable Developer Extras in Blender, Edit -> Preferences -> Interface -> Developer Extras;
- Search by pressing F3, and run Start Debug Server for VS Code;

More info in https://github.com/AlansCodeLog/blender-debugger-for-vscode.


