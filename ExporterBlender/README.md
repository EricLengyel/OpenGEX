# OpenGEX Blender Exporter

This contains an Export plugin for OpenGEX files. 

## Materials

To export materials they must be set up with the `Principled BSDF` shader. The following parameters are currently exported:

* `Base Color` is exported as `diffuse` in the OGEX Material
* `Specular` is exported as `specular`
* `Roughness` is exported as `roughness`
* `Metallic` is exported as `metalness` 
* `Emission` is exported as `emission`. Note that using a separate Emission shader with a Shader Mix is not supported currently.
* `Alpha` is exported as `opacity`. 
* `Normal` is exported as `normal`. Bump/displacement maps are not exported, you must bake these before exporting.

If there are Image textures connected directly to these paramers they will be included in the ogex material.

## Limitations

* UV transforms are ignored in textures.
