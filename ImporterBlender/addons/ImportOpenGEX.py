
import bpy
import os
import sys
import OpenGEX
import Data
import time
import array
import mathutils
import math

from bpy_extras.io_utils import ImportHelper
from bpy_extras.image_utils import load_image
from bpy_extras import node_shader_utils

bl_info = {
	"name": "OpenGEX (.ogex)",
	"description": "Terathon Software's OpenGEX Importer",
	"author": "Miguel Cartaxo",
	"version": (1, 0, 0, 0),
	"blender": (3, 3, 0),
	"location": "File > Import-Export",
	"wiki_url": "http://opengex.org/",
	"category": "Import-Export"}


def texture_image_load(texture_path, default_path, alternative_path):
	image = load_image(texture_path, default_path, recursive=False, relpath=None)

	# If textures are not in the default_path, which should be the same as the .ogex file path then,
	# check the alternative path defined by the user.
	if image is None:
		image = load_image(texture_path, alternative_path, recursive=False, relpath=None)

	return image

def handle_light_attenuation(blender_light, attenuation_struct):
	if not attenuation_struct:
		print("Invalid attenuation structure.")
		return
	
	attenuation_type = attenuation_struct.atten_kind
	curve_type = attenuation_struct.curve_type
	if attenuation_type == "distance":
		if curve_type == "inverse":
			blender_light.falloff_type = "INVERSE_LINEAR"
			blender_light.distance = attenuation_struct.scale_param
		if curve_type == "inverse_square":
			blender_light.falloff_type = "INVERSE_SQUARE"
			blender_light.distance = attenuation_struct.scale_param * attenuation_struct.scale_param
		#if falloff_type == "LINEAR_QUADRATIC_WEIGHTED" #@TODO
	
	if attenuation_type == "angle":
		if curve_type == "linear":
			begin_angle = 1 - (attenuation_struct.begin_param / attenuation_struct.end_param)
			end_angle = attenuation_struct.end_param / 0.5
			blender_light.spot_size = end_angle
			blender_light.spot_blend = begin_angle

# Blender indexes the names of meshes, materials, cameras, etc, by adding a suffix (e.g .001, .002, etc);
# and it does that whenever another mesh (or the respective type) already "exists" with the same name.
# But, it does that even if the mesh has already been deleted and is not part of the existing collection!
# Meaning, there would not be a name conflict. So we set the name again after creation.
#
# Interestingly enough, this does not seem to happen with objects. (e.g with bpy.data.objectsmeshes.new())
#
# To be used after calling bpy.data.meshes.new(), for meshes, after bpy.data.lights.new(), for lights, and so on.
#
# If there is a name conflict, with an actual existing struct in the collection, Blender will automatically
# rename the struct that already exists in the collection, by adding an index like .001, and retain the name of the
# mesh we're forcing the name, the imported struct.
#
# Not 100% this is the best behaviour, but seems to be a reasonable compromise, since we want to keep the correct 
# names if we export a struct and then reimport right after to an empty collection.
def force_name(struct, name):
	print("Force name %s -> %s" % (struct.name, name))
	struct.name = name

class OpenGexImporter(bpy.types.Operator, ImportHelper):
	"""Import to OpenGEX format"""
	bl_idname = "import_scene.ogex"
	bl_label = "Import OpenGEX"
	filename_ext = ".ogex"
	data_description = OpenGEX.OpenGexDataDescription()

	# @Todo We should save this in a file to be reused in different Blender sessions,
	# so that the user does not have to constantly change this every time they restart Blender.
	default_import_path = ""

	use_custom_normals : bpy.props.BoolProperty(name = "Custom Normals", description = "Import custom normals, if available, otherwise Blender will recompute them.", default = True)
	custom_import_path : bpy.props.StringProperty(name = "Texture Path", description = "Define a path here if the textures used by the .ogex file are in a different folder than the .ogex file.", default = default_import_path, maxlen = 260)

	def load_opengex(self, file_path):
		file_size = os.path.getsize(file_path)
		self.file = open(file_path, "r+")
		text_buffer = self.file.read(file_size)
		
		print("Parsing...")
		text_index = 0 # Start of the file.
		result = self.data_description.process_text(text_buffer, text_index)
		
		if result != Data.EDataResult.Okay:
			print("Error: {} in structure {}, line {}" .format(result, self.data_description.error_structure, self.data_description.error_line))
			self.file.close()
			return
		
		self.file.close()

		print("Parsed OpenGex file successfully.")
	
	def execute(self, context):
		print('\nOpenGex import starting... %r' % self.filepath)
		start_time = time.process_time()
		
		# Save set import path for subsequent imports.
		self.default_import_path = self.custom_import_path

		# Parse file.
		self.load_opengex(self.filepath)

		import_path_split = self.filepath.rsplit("\\", 1)
		if len(import_path_split) == 1: # No split happen.
			import_path_split = self.filepath.rsplit("/", 1)

		import_path = import_path_split[0]

		# Import to Blender.
		camera = None
		mesh = None
		object = None
		object_name = ""
		obj_transform = mathutils.Matrix()
		struct_instance = self.data_description.root_structure.first_sub_node
		# @Robustness We should just iterate over the Nodes and skip the Objects,
		# reason being that the Nodes already contain references to the objects
		# so we can handle them while we're handling the Nodes.
		while struct_instance:
			print("Structure: %s - %s" % (struct_instance.name, str(struct_instance.type)))
			if struct_instance.type == OpenGEX.EStructureType.GeometryNode:
				object_name = struct_instance.node_name

				# Traverse sub-nodes of GeometryNode as they contain references to other nodes
				# related to this GeometryNode.
				sub_struct = struct_instance.first_sub_node
				while sub_struct:
					if sub_struct.type == OpenGEX.EStructureType.Transform:
						t = sub_struct.matrix_value
						obj_transform[0][0:3] = t.m00, t.m01, t.m02, t.m03
						obj_transform[1][0:3] = t.m10, t.m11, t.m12, t.m13
						obj_transform[2][0:3] = t.m20, t.m21, t.m22, t.m23
						obj_transform[3][0:3] = t.m30, t.m31, t.m32, t.m33
						obj_transform.transpose() # @Robustness Should not have to transpose.
					
					sub_struct = sub_struct.next_node


			# Geometry data.
			if struct_instance.type == OpenGEX.EStructureType.GeometryObject:
				mesh_struct = struct_instance.mesh_map.get(0) # @Incomplete Only deal with LOD 0
				if mesh_struct:
					vertices = []
					indices = []
					indices_list = []
					normals = []
					texcoords = []
					for vertex_array in mesh_struct.vertex_array_list:
						if vertex_array.attrib_string == "position":
							vertices = vertex_array.vertex_array_data

						if vertex_array.attrib_string == "normal":
							normals = vertex_array.vertex_array_data
						
						if vertex_array.attrib_string == "texcoord":
							texcoords = vertex_array.vertex_array_data
					
					for index_array in mesh_struct.index_array_list:
						indices = index_array.index_array_data
						indices_list = index_array.array_storage

					mesh = bpy.data.meshes.new(struct_instance.name)
					force_name(mesh, struct_instance.name)
					
					mesh.from_pydata(vertices, [], indices)
					
					mesh.uv_layers.new(do_init=False)
					texcoord_to_index = []
					for index in indices_list:
						texcoord = texcoords[index]
						texcoord_to_index.append(texcoord[0])
						texcoord_to_index.append(texcoord[1])
					mesh.uv_layers[0].data.foreach_set("uv", texcoord_to_index)

					ok_normals = False
					if self.use_custom_normals:
						# Note: we store 'temp' normals in loops, since validate() may alter final mesh,
						#       we can only set custom lnors *after* calling it.
						mesh.create_normals_split()
						normals_to_index = []
						for index in indices_list:
							normal = normals[index]
							normals_to_index.append(normal[0])
							normals_to_index.append(normal[1])
							normals_to_index.append(normal[2])
						mesh.loops.foreach_set("normal", normals_to_index)
						ok_normals = True


					mesh.validate(verbose=True, clean_customdata=False) # *Very* important to not remove lnors here!

					if ok_normals:
						# Re-apply normals
						clnors = array.array('f', [0.0] * (len(mesh.loops) * 3))
						mesh.loops.foreach_get("normal", clnors)

						#unique_smooth_groups = False
						#if not unique_smooth_groups:
						mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

						mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
						mesh.use_auto_smooth = True
						mesh.free_normals_split()
					else:
						mesh.calc_normals()

					#if not unique_smooth_groups:
					mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

					mesh.update()


					object = bpy.data.objects.new(object_name, mesh)
					bpy.context.collection.objects.link(object)
					object.matrix_world = obj_transform
					bpy.context.view_layer.objects.active = object
					object.select_set(True)


			# Material data.
			if struct_instance.type == OpenGEX.EStructureType.Material:
				material_name = struct_instance.material_name
				material = bpy.data.materials.new(material_name)
				force_name(material, material_name)

				material_wrap = node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False)
				material_wrap.use_nodes = True

				# @Note Material Spectra currently not supported.
				
				for color_struct in struct_instance.colors:
					color = color_struct.color
					if color_struct.attrib_string == "diffuse" or color_struct.attrib_string == "albedo":
						material_wrap.base_color = (color.x, color.y, color.z)
					
					if color_struct.attrib_string == "specular":
						# OpenGex specifies specular as a color, but Blender treats it as a float factor.
						material_wrap.specular = color.x

					if color_struct.attrib_string == "emission":
						material_wrap.emission_color = (color.x, color.y, color.z)

				for param_struct in struct_instance.params:
					if param_struct.attrib_string == "roughness":
						material_wrap.roughness = param_struct.param
					
					if param_struct.attrib_string == "metalness":
						material_wrap.metallic = param_struct.param
					
					if param_struct.attrib_string == "opacity":
						material_wrap.alpha = param_struct.param

				for texture_struct in struct_instance.textures:
					loaded_image = texture_image_load(texture_struct.texture_name, import_path, self.custom_import_path)
					if loaded_image is None:
						if self.custom_import_path:
							print("Failed to load image %s from %s and %s" % (texture_struct.texture_name, import_path, self.custom_import_path))
						else:
							print("Failed to load image %s from %s" % (texture_struct.texture_name, import_path))

						continue

					if texture_struct.attrib_string == "diffuse" or texture_struct.attrib_string == "albedo":
						material_wrap.base_color_texture.image = loaded_image
						material_wrap.base_color_texture.texcoords = 'UV'
					
					elif texture_struct.attrib_string == "specular":
						material_wrap.specular_texture.image = loaded_image
						material_wrap.specular_texture.texcoords = 'UV'
					
					elif texture_struct.attrib_string == "emission":
						material_wrap.emission_color_texture.image = loaded_image
						material_wrap.emission_color_texture.texcoords = 'UV'
					
					elif texture_struct.attrib_string == "metallic":
						material_wrap.metallic_texture.image = loaded_image
						material_wrap.metallic_texture.texcoords = 'UV'
					
					elif texture_struct.attrib_string == "roughness":
						material_wrap.roughness_texture.image = loaded_image
						material_wrap.roughness_texture.texcoords = 'UV'
					
					elif texture_struct.attrib_string == "normal":
						material_wrap.normalmap_texture.image = loaded_image
						material_wrap.normalmap_texture.texcoords = 'UV'

				if mesh:
					mesh.materials.append(material)
				else:
					print('Error: Mesh is invalid while processing material.')


			# Light data.
			if struct_instance.type == OpenGEX.EStructureType.LightNode:
				light_object_name = struct_instance.node_name
				light_struct = struct_instance.light_object_structure
				if light_struct:
					light_type = "POINT"
					if light_struct.type_string == "infinite":
						light_type = "SUN"
					if light_struct.type_string == "point":
						light_type = "POINT"							
					if light_struct.type_string == "spot":
						light_type = "SPOT"
					
					light = bpy.data.lights.new(name=light_struct.name, type=light_type)
					force_name(light, light_struct.name)

					light.use_shadow = light_struct.shadow_flag
					light.energy = light_struct.intensity
					light.shadow_soft_size = light_struct.radius # Odd naming for light radius.
					if light_type == "SUN":
						light.angle = light_struct.angle
					light.color = (light_struct.color.x, light_struct.color.y, light_struct.color.z)

					# Handle Attenuation
					# @NOTE This data should have already been available during parsing
					# instead of being handled here? (thinking_face)
					for attenuation_struct in light_struct.attenuations:
						handle_light_attenuation(light, attenuation_struct)

					light_object = bpy.data.objects.new(light_object_name, light)
					bpy.context.collection.objects.link(light_object)

					light_transform = mathutils.Matrix()
					# Traverse sub-nodes of LightNode as they contain references to other nodes
					# related to this LightNode.
					sub_struct = struct_instance.first_sub_node
					while sub_struct:
						if sub_struct.type == OpenGEX.EStructureType.Transform:
							t = sub_struct.matrix_value
							light_transform[0][0:3] = t.m00, t.m01, t.m02, t.m03
							light_transform[1][0:3] = t.m10, t.m11, t.m12, t.m13
							light_transform[2][0:3] = t.m20, t.m21, t.m22, t.m23
							light_transform[3][0:3] = t.m30, t.m31, t.m32, t.m33
							light_transform.transpose() # @Robustness Should not have to transpose.
						
						sub_struct = sub_struct.next_node
					
					light_object.matrix_world = light_transform
			

			# Camera data.
			if struct_instance.type == OpenGEX.EStructureType.CameraNode:
				camera_object_name = struct_instance.node_name
				camera_struct = struct_instance.camera_object_structure
				# @TODO Only perspective is suppported. Add support for orthographic and panoramic cameras.
				if camera_struct:
					camera = bpy.data.cameras.new(name=camera_struct.name)
					force_name(camera, camera_struct.name)

					camera.clip_start = camera_struct.near_depth
					camera.clip_end = camera_struct.far_depth

					t = 1.0 / camera_struct.projection_distance
					at = math.atan(t) / 0.5 * self.data_description.angle_scale
					camera.angle_y = at

					camera_object = bpy.data.objects.new(camera_object_name, camera)
					bpy.context.collection.objects.link(camera_object)

					camera_transform = mathutils.Matrix()
					# Traverse sub-nodes of CameraNode as they contain references to other nodes
					# related to this CameraNode.
					sub_struct = struct_instance.first_sub_node
					while sub_struct:
						if sub_struct.type == OpenGEX.EStructureType.Transform:
							t = sub_struct.matrix_value
							camera_transform[0][0:3] = t.m00, t.m01, t.m02, t.m03
							camera_transform[1][0:3] = t.m10, t.m11, t.m12, t.m13
							camera_transform[2][0:3] = t.m20, t.m21, t.m22, t.m23
							camera_transform[3][0:3] = t.m30, t.m31, t.m32, t.m33
							camera_transform.transpose() # @Robustness Should not have to transpose.
						
						sub_struct = sub_struct.next_node
					
					camera_object.matrix_world = camera_transform

			struct_instance = struct_instance.next_node
		
		self.data_description.__init__() # Reset description.

		print('Import finished in %.4f sec.' % (time.process_time() - start_time))
		return {'FINISHED'}


# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------


def menu_func(self, context):
	self.layout.operator(OpenGexImporter.bl_idname, text = "OpenGEX (.ogex)")

def register():
	bpy.utils.register_class(OpenGexImporter)
	bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
	bpy.types.TOPBAR_MT_file_import.remove(menu_func)
	bpy.utils.unregister_class(OpenGexImporter)

if __name__ == "__main__":
	register()