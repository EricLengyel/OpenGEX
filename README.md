# Open Game Engine Exchange

This repository contains reference code for the Open Game Engine Exchange (OpenGEX) file format.

For more information about OpenGEX, see [opengex.org](http://opengex.org).

## Export Plugins

To use the export plugin for 3ds Max, place the OpenGex.dle file in the Max `plugins` directory.

To use the export plugin for Maya, place the OpenGex.mll file in the Maya `bin/plug-ins` directory.

To use the export plugin for Blender, either add the `ExportBlender` path to your script path in Preferences, or use the `Install` button in the Preferences, Add-ons panel and locate the `ExportOpenGEX.py` file. 

## Import Template

The reference importer contains a lot of code that reads an OpenGEX file, validates it, and creates all of the structures necessary to construct a scene. Application-specific processing must be added in the appropriate places to support your own software.
