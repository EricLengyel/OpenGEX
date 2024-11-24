from enum import Enum
import OpenDDL
import Data
import VMath
from VMath import Vector2D
from VMath import Vector3D
from VMath import Vector4D
from VMath import Matrix3D
from VMath import Matrix4D
from VMath import Qtrn
import math
import sys


class EStructureType(Enum):
	# See StructureType enum in OpenDDL.py.
	Metric          = 5,
	Name            = 6,
	ObjectRef       = 7,
	MaterialRef     = 8,
	Matrix          = 9,
	Transform       = 10,
	Translation     = 11,
	Rotation        = 12,
	Scale           = 13,
	MorphWeight     = 14,
	Node            = 15,
	BoneNode        = 16,
	GeometryNode    = 17,
	LightNode       = 18,
	CameraNode      = 19,
	VertexArray     = 20,
	IndexArray      = 21,
	BoneRefArray    = 22,
	BoneCountArray  = 23,
	BoneIndexArray  = 24,
	BoneWeightArray = 25,
	Skeleton        = 26,
	Skin            = 27,
	Morph           = 28,
	Mesh            = 29,
	Object          = 30,
	GeometryObject  = 31,
	LightObject     = 32,
	CameraObject    = 33,
	Attrib          = 34,
	Param           = 35,
	Color           = 36,
	Spectrum        = 37,
	Texture         = 38,
	Atten           = 39,
	Material        = 40,
	Key             = 41,
	Curve           = 42,
	Time            = 43,
	Value           = 44,
	Track           = 45,
	Animation       = 46,
	Clip            = 47


class EDataResult(Enum):
	InvalidUpDirection			= 5,  # Metric has invalid up direction
	InvalidForwardDirection		= 6,  # Metric has invalid forward direction.
	InvalidTranslationKind		= 7,  # Invalid translation kind.
	InvalidRotationKind			= 8,  # Invalid rotation kind.
	InvalidScaleKind			= 9,  # Invalide scale kind.
	DuplicateLod				= 10, # Geometry object has a duplicate LOD.
	MissingLodSkin				= 11, # Geometry object has missing LOD skin.
	MissingLodMorph				= 12, # Geometry object has missing LOD morph.
	DuplicateMorph				= 13, # Geometry object has a duplicate morph.
	UndefinedLightType			= 14, # Light object has undefined light type.
	UndefinedCurve				= 15, #  Light object has undefined curve for attenuation.
	UndefinedAtten				= 16, # Light object has undefined attenuation.
	DuplicateVertexArray		= 17, # Duplicate vertex array.
	PositionArrayRequired		= 18, # Position array required.
	VertexCountUnsupported		= 19, # Vertex count unsupported.
	IndexValueUnsupported		= 20, # Index value unsupported.
	IndexArrayRequired			= 21, # Index array required.
	VertexCountMismatch			= 22, # Vertex count mismatch.
	BoneCountMismatch			= 23, # Skeleton has bone count mismatch.
	BoneWeightCountMismatch		= 24, # Skin has bone weight count mismatch.
	InvalidBoneRef				= 25, # Bone reference array has invalid bone reference.
	InvalidObjectRef			= 26, # Node structure has invalid object reference.
	InvalidMaterialRef			= 27, # Material reference structure has invalid material reference.
	MaterialIndexUnsupported	= 28, # Geometry node has more materials than we support (256).
	DuplicateMaterialRef		= 29, # Geometry node has duplicate material reference.
	MissingMaterialRef			= 30, # Geometry node has missing material reference.
	TargetRefNotLocal			= 31, # Track structure's target reference is not local.
	InvalidTargetStruct			= 32, # Track structure has invalid target structure.
	InvalidKeyKind				= 33, # Curve or Key structure has invalid key kind.
	InvalidCurveType			= 34, # Invalid curve type.
	KeyCountMismatch			= 35, # Key count mismatch.
	EmptyKeyStructure			= 36  # Key structure is empty.


# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class OpenGexStructure(OpenDDL.Structure):
	def __init__(self, in_type):
		super().__init__(in_type)

	def validate_substructure(self, data_description, struct_instance):
		super().validate_substructure(data_description, struct_instance)

	def validate_property(self, data_description, identifier):
		super().validate_property(data_description, identifier)

	def set_property(self, data_description, identifier, data_value):
		super().set_property(data_description, identifier, data_value)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class NodeStructure(OpenGexStructure):
	def __init__(self, type = EStructureType.Node):
		super().__init__(type)
		self.set_base_structure_type(EStructureType.Node)
		self.node_name = None
		self.node_transform = Matrix4D()
		self.object_transform = Matrix4D()
		self.inverse_object_transform = Matrix4D()

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.base_type
		if local_type == EStructureType.Node or local_type == EStructureType.Matrix:
			return True

		local_type = struct_instance.type
		if local_type == EStructureType.Name or local_type == EStructureType.Animation:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		local_struct = self.get_first_substructure(EStructureType.Name)
		if local_struct:
			if self.get_last_substructure(EStructureType.Name) != local_struct:
				return OpenDDL.EDataResult.ExtraneousSubstructure

			self.node_name = local_struct.name
		else:
			self.node_name = None

		return Data.EDataResult.Okay

	def get_object_structure(self):
		return None

	def calculate_node_transforms(self, data_description):
		self.node_transform.set_identity()
		self.object_transform.set_identity()

		object_struct = self.get_object_structure()

		local_struct = self.first_sub_node
		while local_struct:
			if local_struct.base_type == EStructureType.Matrix:
				if local_struct.object_flag:
					self.node_transform = self.node_transform * local_struct.matrix_value
				elif object_struct:
					self.object_transform = self.object_transform * local_struct.matrix_value

			local_struct = local_struct.next_node

		self.node_transform = data_description.adjust_transform(self.node_transform)
		self.object_transform = data_description.adjust_transform(self.object_transform)

		self.inverse_object_transform = VMath.inverse_matrix4D(self.object_transform)

	def update_node_transforms(self, data_description):
		self.calculate_node_transforms(data_description)

		local_struct = self.first_sub_node
		while local_struct:
			if local_struct.base_type == EStructureType.Node:
				local_struct.update_node_transforms(data_description)

			local_struct = local_struct.next_node

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class BoneNodeStructure(NodeStructure):
	def __init__(self):
		super().__init__(EStructureType.BoneNode)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class AttribStructure(OpenGexStructure):
	def __init__(self, in_type):
		super().__init__(in_type)
		self.set_base_structure_type(EStructureType.Attrib)
		self.attrib_string = ""

	def validate_substruct(self, data_description, struct_instance):
		super().validate_substructure(data_description, struct_instance)

	def validate_property(self, data_description, identifier):
		if identifier == "attrib":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "attrib":
			self.attrib_string = data_value
			return True

		return False

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ParamStructure(AttribStructure):
	def __init__(self):
		super().__init__(EStructureType.Param)
		self.param = 0.0

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return struct_instance.array_size == 0

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(struct_instance.data_array) == 1:
			self.param = struct_instance.data_array[0]
		else:
			return OpenDDL.EDataResult.InvalidDataFormat

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ColorStructure(AttribStructure):
	def __init__(self):
		super().__init__(EStructureType.Color)
		self.color = Vector4D(Vector3D(1.0, 1.0, 1.0), 1.0) # Should be separate struct :(

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return (struct_instance.array_size - 3) < 2

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		array_size = struct_instance.array_size
		if len(struct_instance.data_array) == array_size:
			if array_size == 3:
				color = Vector3D(struct_instance.data_array[0], struct_instance.data_array[1], struct_instance.data_array[2])
				#color = data_description.convert_color(color)
				self.color = Vector4D(color, 1.0)
			else:
				color = Vector3D(struct_instance.data_array[0], struct_instance.data_array[1], struct_instance.data_array[2])
				#color = data_description.convert_color(color)
				self.color = Vector4D(color, struct_instance.data_array[3])
		else:
			return OpenDDL.EDataResult.InvalidDataFormat

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class SpectrumStructure(AttribStructure):
	def __init__(self):
		super().__init__(EStructureType.Spectrum)
		self.wave_length_min = 0
		self.wave_length_max = 0

	def validate_property(self, data_description, identifier):
		
		return super().validate_property(data_description, identifier)

	def set_property(self, data_description, identifier, data_value):
		return super().validate_property(data_description, identifier, data_value)

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return struct_instance.array_size == 0

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		# Process spectrum here.

		return Data.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class TextureStructure(AttribStructure):
	def __init__(self):
		super().__init__(EStructureType.Texture)
		self.texcoord_index = 0
		self.texture_swizzle = "i"
		self.texture_address = ["repeat", "repeat", "repeat"]
		self.texture_border = "zero"
		self.texture_name = ""
		self.texcoord_transform = Matrix4D()
		self.texcoord_transform.set_identity()

	def validate_property(self, data_description, identifier):
		if identifier == "texcoord":
			return True, Data.EDataType.UInt32

		if identifier == "swizzle":
			return True, Data.EDataType.String

		if identifier == "x_address":
			return True, Data.EDataType.String

		if identifier == "y_address":
			return True, Data.EDataType.String

		if identifier == "z_address":
			return True, Data.EDataType.String

		if identifier == "border":
			return True, Data.EDataType.String

		return super().validate_property(data_description, identifier)

	def set_property(self, data_description, identifier, data_value):
		if identifier == "texcoord":
			self.texcoord_index = data_value
			return True

		if identifier == "swizzle":
			self.texture_swizzle = data_value
			return True

		if identifier == "x_address":
			self.texture_address[0] = data_value
			return True

		if identifier == "y_address":
			self.texture_address[1] = data_value
			return True

		if identifier == "z_address":
			self.texture_address[2] = data_value
			return True

		if identifier == "border":
			self.texture_border = data_value
			return True

		return super().set_property(data_description, identifier, data_value)

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.type
		if local_type == Data.EDataType.String or local_type == EStructureType.Animation or struct_instance.base_type == EStructureType.Matrix:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		name_flag = False

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == Data.EDataType.String:
				if name_flag == False:
					name_flag = True
					if len(struct_instance.data_array) == 1:
						self.texture_name = struct_instance.data_array[0]
					else:
						return OpenDDL.EDataResult.InvalidDataFormat

				else:
					return OpenDDL.EDataResult.ExtraneousSubstructure
			elif struct_instance.base_type == EStructureType.Matrix:
				self.texcoord_transform = self.texcoord_transform * struct_instance.matrix_value

			struct_instance = struct_instance.next_node

		if name_flag == False:
			return OpenDDL.EDataResult.MissingSubstructure

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class AttenStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Atten)
		self.atten_kind = "distance"
		self.curve_type = "linear"
		self.begin_param = 0.0
		self.end_param = 1.0
		self.scale_param = 1.0
		self.offset_param = 0.0
		self.constant_param = 0.0
		self.linear_param = 0.0
		self.quadratic_param = 1.0
		self.power_param = 1.0

	def validate_property(self, data_description, identifier):
		if identifier == "kind":
			return True, Data.EDataType.String

		if identifier == "curve":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "kind":
			self.atten_kind = data_value
			return True

		if identifier == "curve":
			self.curve_type = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.Param:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if self.curve_type == "inverse":
			self.linear_param = 1.0

		distance_scale = data_description.distance_scale
		angle_scale = data_description.angle_scale

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == EStructureType.Param:
				if struct_instance.attrib_string == "begin":
					self.begin_param = struct_instance.param

					if self.atten_kind == "distance":
						self.begin_param *= distance_scale
					elif self.atten_kind == "angle":
						self.begin_param *= angle_scale
				elif struct_instance.attrib_string == "end":
					self.end_param = struct_instance.param

					if self.atten_kind == "distance":
						self.end_param *= distance_scale
					elif self.atten_kind == "angle":
						self.end_param *= angle_scale
				elif struct_instance.attrib_string == "scale":
					self.scale_param = struct_instance.param

					if self.atten_kind == "distance":
						self.scale_param *= distance_scale
					elif self.atten_kind == "angle":
						self.scale_param *= angle_scale
				elif struct_instance.attrib_string == "offset":
					self.offset_param = struct_instance.param
				elif struct_instance.attrib_string == "constant":
					self.constant_param = struct_instance.param
				elif struct_instance.attrib_string == "linear":
					self.linear_param = struct_instance.param
				elif struct_instance.attrib_string == "quadratic":
					self.quadratic_param = struct_instance.param
				elif struct_instance.attrib_string == "power":
					self.power_param = struct_instance.param

			struct_instance = struct_instance.next_node

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MaterialStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Material)
		self.two_sided_flag = False
		self.material_name = ""
		self.colors = []
		self.params = []
		self.textures = []
		self.spectra = []

	def validate_property(self, data_description, identifier):
		if identifier == "two_sided":
			return True, Data.EDataType.Bool

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "two_sided":
			self.two_sided_flag = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.base_type == EStructureType.Attrib or struct_instance.type == EStructureType.Name:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		struct_instance = self.get_first_substructure(EStructureType.Name)
		if struct_instance:
			if self.get_last_substructure(EStructureType.Name) != struct_instance:
				return OpenDDL.EDataResult.ExtraneousSubstructure

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == EStructureType.Name:
				self.material_name = struct_instance.name
			elif struct_instance.type == EStructureType.Color:
				self.colors.append(struct_instance)
			elif struct_instance.type == EStructureType.Param:
				self.params.append(struct_instance)
			elif struct_instance.type == EStructureType.Texture:
				self.textures.append(struct_instance)
			elif struct_instance.type == EStructureType.Spectrum:
				self.spectra.append(struct_instance)
			
			struct_instance = struct_instance.next_node
		
		# Do application-specific material processing here.

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class KeyStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Key)
		self.key_kind = "value"
		self.scalar_flag = False

	def validate_property(self, data_description, identifier):
		if identifier == "kind":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "kind":
			self.key_kind = data_value
			return True

		return False
		
	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		structure = self.first_sub_node
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(structure.data_array) == 0:
			return EDataResult.EmptyKeyStructure

		if self.key_kind == "value" or self.key_kind == "-control" or self.key_kind == "+control":
			self.scalar_flag = False
		elif self.key_kind == "tension" or self.key_kind == "continuity" or self.key_kind == "bias":
			self.scalar_flag = True
			
			if structure.array_size != 0:
				return OpenDDL.EDataResult.InvalidDataFormat

		else:
			return EDataResult.InvalidKeyKind

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class CurveStructure(OpenGexStructure):
	def __init__(self, type):
		super().__init__(type)
		self.base_type = EStructureType.Curve
		self.curve_type = "linear"
		self.key_value_structure = None
		self.key_control_structure = [None] * 2
		self.key_tension_structure = None
		self.key_continuity_structure = None
		self.key_bias_structure = None
		self.key_data_element_count = 0

	def validate_property(self, data_description, identifier):
		if identifier == "curve":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "curve":
			self.curve_type = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.Key:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		self.key_value_structure = None
		self.key_control_structure[0] = None
		self.key_control_structure[1] = None
		self.key_tension_structure = None
		self.key_continuity_structure = None
		self.key_bias_structure = None

		structure = self.first_sub_node
		while structure:
			if structure.type == EStructureType.Key:
				if structure.key_kind == "value":
					if not self.key_value_structure:
						self.key_value_structure = structure
					else:
						return OpenDDL.EDataResult.ExtraneousStructure

				elif structure.key_kind == "-control":
					if self.curve_type != "bezier":
						return EDataResult.InvalidKeyKind

					if not self.key_control_structure[0]:
						self.key_control_structure[0] = structure
					else:
						return OpenDDL.EDataResult.Extraneous_Substructure
				
				elif structure.key_kind == "+control":
					if self.curve_type != "bezier":
						return EDataResult.InvalidKeyKind

					if not self.key_control_structure[1]:
						self.key_control_structure[1] = structure
					else:
						return OpenDDL.EDataResult.ExtraneousSubstructure

				elif structure.key_kind == "tension":
					if self.curve_type != "tcb":
						return EDataResult.InvalidKeyKind

					if not self.key_tension_structure:
						self.key_tension_structure = structure
					else:
						return OpenDDL.EDataResult.ExtraneousSubstructure

				elif structure.key_kind == "continuity":
					if self.curve_type != "tcb":
						return EDataResult.InvalidKeyKind

					if not self.key_continuity_structure:
						self.key_continuity_structure = structure
					else:
						return OpenDDL.EDataResult.ExtraneousSubstructure

				elif structure.key_kind == "bias":
					if self.curve_type != "tcb":
						return EDataResult.InvalidKeyKind

					if not self.key_bias_structure:
						self.key_bias_structure = structure
					else:
						return OpenDDL.EDataResult.ExtraneousSubstructure

			structure = structure.next_node

		if not self.key_value_structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.curve_type == "bezier":
			if not self.key_control_structure[0] or self.key_control_structure[1]:
				return OpenDDL.EDataResult.MissingSubstructure

		elif self.curve_type == "tcb":
			if not self.key_tension_structure or not self.key_continuity_structure or not self.key_bias_structure:
				return OpenDDL.EDataResult.MissingSubstructure
		
		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class TimeStructure(CurveStructure):
	def __init__(self):
		super().__init__(EStructureType.Time)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if self.curve_type != "linear" and self.curve_type != "bezier":
			return EDataResult.InvalidCurveType

		element_count = 0
		structure = self.first_sub_node

		while structure:
			if structure.type == EStructureType.Key:
				data_structure = structure.first_sub_node
				if data_structure.array_size != 0:
					return OpenDDL.InvalidFormat

				count = len(data_structure.data_array)
				if element_count == 0:
					element_count = count
				elif count != element_count:
					return EDataResult.KeyCountMismatch

			structure = structure.next_node

		self.key_data_element_count = element_count
		return Data.EDataResult.Okay

	def calculate_interpolation_parameter(self, time):
		value_structure = self.key_value_structure.first_sub_node
		value = value_structure.data_array[0]
		
		count = self.key_data_element_count
		index = 0

		while index < count:
			if time < value[index]:
				break
			index += 1

		param = 0.0
		if index > 0 and index < count:
			t0 = value[index - 1]
			t3 = value[index]

			u = 0.0
			dt = t3 - t0
			if dt > sys.float_info.min:
				u = (time - t0) / dt

			if self.curve_type == "bezier":
				t1 = self.key_control_structure[1].first_sub_node.data_array[index - 1]
				t2 = self.key_control_structure[0].first_sub_node.data_array[index]

				a0 = dt + (t1 - t2) * 3.0
				a1 = a0 * 3.0
				b0 = 3.0 * (t0 - t1 * 2.0 + t2)
				b1 = b0 * 2.0
				c = (t1 - t0) * 3.0
				d = t0 - time

				k = 0
				while k < 3:
					u = VMath.saturate(u - ((((a0 * u) + b0) * u + c) * u + d) / (((a1 * u) + b1) * u + c))
					k += 1

			param = u
		else:
			param = 0.0

		return index - 1, param

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ValueStructure(CurveStructure):
	def __init__(self):
		super().__init__(EStructureType.Value)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if self.curve_type != "constant" and self.curve_type != "linear" and self.curve_type != "bezier" and self.curve_type != "tcb":
			return EDataResult.InvalidCurveType

		target_structure = self.super_node.target_structure.first_sub_node
		if target_structure and target_structure.type == Data.EDataType.Float:
			target_array_size = target_structure.array_size
			element_count = 0

			structure = self.first_sub_node
			while structure:
				if structure.type == EStructureType.Key:
					data_structure = structure.first_sub_node
					array_size = data_structure.array_size

					if structure.scalar_flag and array_size != target_array_size:
						return OpenDDL.EDataResult.InvalidDataFormat

					count = len(data_structure.data_array) / max(array_size, 1)
					if element_count == 0:
						element_count = count
					elif count != element_count:
						return EDataResult.KeyCountMismatch

				structure = structure.next_node

			self.key_data_element_count = element_count

		return Data.EDataResult.Okay
		

	def update_animation(self, data_description, index, param, target):
		data = [None] * 16
		values = self.key_value_structure.first_sub_node.data_array

		count = self.key_data_element_count
		array_size = max(target.first_sub_node.array_size, 1)

		if index < 0:
			target.update_animation(data_description, values)

		elif index >= count - 1:
			target.update_animation(data_description, values[array_size * (count -1):])
		else:
			p1 = array_size * index

			if self.curve_type == "constant":
				k = 0
				while k < array_size:
					data[k] = values[p1 + k]
					k += 1
			
			else:
				p2 = p1 + array_size
				u = 1.0 - param
				
				if self.curve_type == "linear":
					k = 0
					while k < array_size:
						data[k] = values[p1 + k] * u + values[p2 + k] * param
						k += 1
				
				elif self.curve_type == "bezier":
					c1_values = self.key_control_structure[1].first_sub_node.data_array[array_size * index:]
					c2_values = self.key_control_structure[0].first_sub_node.data_array[array_size * (index + 1):]

					u2 = u * u
					u3 = u2 * u
					v2 = param * param
					v3 = v2 * param
					f1 = u2 * param * 3.0
					f2 = u * v2 * 3.0

					k = 0
					while k < array_size:
						data[k] = values[p1 + k] * u3 + c1_values[k] * f1 + c2_values[k] * f2 + values[p2 + k] * v3
						k += 1

				else:
					p0 = array_size * max(index - 1, 0)
					p3 = array_size * min(index + 2, count - 1)

					tension = self.key_tension_structure.first_sub_node.data_array
					continuity = self.key_continuity_structure.first_sub_node.data_array
					bias = self.key_bias_structure.first_sub_node.data_array

					m1 = (1.0 - tension[index]) * (1.0 + continuity[index]) * (1.0 + bias[index]) * 0.5
					n1 = (1.0 - tension[index]) * (1.0 - continuity[index]) * (1.0 - bias[index]) * 0.5

					m2 = (1.0 - tension[index + 1]) * (1.0 - continuity[index + 1]) * (1.0 + bias[index + 1]) * 0.5
					n2 = (1.0 - tension[index + 1]) * (1.0 + continuity[index + 1]) * (1.0 - bias[index + 1]) * 0.5

					u2 = u * u
					v2 = param * param
					v3 = v2 * param
					f1 = 1.0 - v2 * 3.0 + v3 * 2.0
					f2 = v2 * (3.0 - param * 2.0)
					f3 = param * u2
					f4 = u * v2

					k = 0
					while k < array_size:
						t1 = (values[p1 + k] - values[p0 + k]) * m1 + (values[p2 + k] - values[p1 + k]) * n1
						t2 = (values[p2 + k] - values[p1 + k]) * m2 + (values[p3 + k] - values[p2 + k]) * n2

						data[k] = values[p1 + k] * f1 + values[p2 + k] * f2 + t1 * f3 - t2 * f4
						k += 1

			target.update_animation(data_description, data)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class TrackStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Track)
		self.target_ref = None
		self.target_structure = None
		self.time_structure = None
		self.value_structure = None

	def validate_property(self, data_description, identifier):
		if identifier == "target":
			return True, Data.EDataType.Ref

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "target":
			self.target_ref = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.base_type == EStructureType.Curve:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		if self.target_ref.is_ref_global:
			return EDataResult.TargetRefNotLocal

		target = self.super_node.super_node.find_structure(self.target_ref)
		if not target:
			return OpenDDL.EDataResult.BrokenRef

		if target.base_type != EStructureType.Matrix and target.type != EStructureType.MorphWeigh:
			return Data.EDataResult.InvalidTargetStruct

		self.target_structure = target
		self.time_structure = None
		self.value_structure = None
		
		structure = self.first_sub_node
		while structure:
			type = structure.type
			if type == EStructureType.Time:
				if not self.time_structure:
					self.time_structure = structure
				else:
					return OpenDDL.EDataResult.ExtraneousSubstructure

			elif type == EStructureType.Value:
				if not self.value_structure:
					self.value_structure = structure
				else:
					return OpenDDL.EDataResult.ExtraneousSubstructure

			structure = structure.next_node

		if not self.time_structure or not self.value_structure:
			return OpenDDL.EDataResult.MissingSubstructure

		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if self.time_structure.key_data_element_count != self.value_structure.key_data_element_count:
			return EDataResult.KeyCountMismatch

		self.super_node.track_list.append(self)
		return Data.EDataResult.Okay

	def update_animation(self, data_description, time):
		index, param = self.time_structure.calculate_interpolation_parameter(time)
		self.value_structure.update_animation(data_description, index, param, self.target_structure)
		
# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class Range:
	def __init__(self, minimum, maximum):
		self.min = minimum
		self.max = maximum

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class AnimationStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Animation)
		self.clip_index = 0
		self.begin_flag = False
		self.end_flag = False
		self.begin_time = 0.0
		self.end_time = 0.0
		self.track_list = []

	def validate_property(self, data_description, identifier):
		if identifier == "clip":
			return True, Data.EDataType.UInt32

		if identifier == "begin":
			self.begin_flag = True
			return True, Data.EDataType.Float

		if identifier == "end":
			self.end_flag = True
			return True, Data.EDataType.Float

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "clip":
			self.clip_index = data_value
			return True

		if identifier == "begin":
			self.begin_time = data_value
			return True

		if identifier == "end":
			self.end_time = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.Track:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if len(self.track_list) == 0:
			return OpenDDL.EDataResult.MissingSubstructure

		data_description.animation_list.append(self)
		return Data.EDataResult.Okay

	def get_animation_time_range(self):
		min_t = sys.float_info.max
		max_t = 0.0

		for node in self.track_list:
			track_structure = node.data
			key_structure = track_structure.time_structure.key_value_structure
			data_structure = key_structure.first_sub_node

			min_t = min(min_t, data_structure.data_array[0])
			max_t = max(max_t, data_structure.data_array[len(data_structure.data_array) - 1])

		if self.begin_flag:
			min_t = self.begin_time

		if self.end_flag:
			max_t = self.end_time

		return Range(min_t, max(min_t, max_t))

	def update_animation(self, data_description, time):
		if self.begin_flag:
			time = max(time, self.begin_time)
		
		if self.end_flag:
			time = min(time, self.end_time)

		for node in self.track_list:
			track_structure = node.data
			track_structure.update_animation(data_description, time)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ClipStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Clip)
		self.clip_index = 0
		self.frame_rate = 0.0
		self.clip_name = None

	def validate_property(self, data_description, identifier):
		if identifier == "index":
			return True, Data.EDataType.UInt32

	def set_property(self, data_description, identifier, data_value):
		if identifier == "index":
			self.clip_index = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == EStructureType.Name or type == EStructureType.Param:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		self.frame_rate = 0.0
		clip_name = None

		structure = self.first_sub_node
		while structure:
			type = structure.type
			if type == EStructureType.Name:
				if self.clip_name:
					return OpenDDL.EDataResult.ExtraneousSubstructure

				self.clip_name = structure.name

			elif type == EStructureType.Param:
				if structure.attrib_string == "rate":
					self.frame_rate = structure.param

			structure = structure.next_node

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MeshStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Mesh)
		self.mesh_level = 0
		self.mesh_primitive = ""
		self.vertex_array_list = []
		self.index_array_list = []
		self.skin_struct = None

	def validate_property(self, data_description, identifier):
		if identifier == "lod":
			return True, Data.EDataType.UInt32

		if identifier == "primitive":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "lod":
			self.mesh_level = data_value
			return True

		if identifier == "primitive":
			self.mesh_primitive = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.type
		if local_type == EStructureType.VertexArray or local_type == EStructureType.IndexArray or local_type == EStructureType.Skin:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		struct_instance = self.first_sub_node
		while struct_instance:
			local_type = struct_instance.type
			if local_type == EStructureType.VertexArray:
				self.vertex_array_list.append(struct_instance)
				
			elif local_type == EStructureType.IndexArray:
				self.index_array_list.append(struct_instance)

			elif local_type == EStructureType.Skin:
				if self.skin_struct:
					return OpenDDL.EDataResult.ExtraneousSubstructure

				self.skin_struct = struct_instance

			struct_instance = struct_instance.next_node

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ObjectStructure(OpenGexStructure):
	def __init__(self, in_type):
		super().__init__(in_type)
		self.set_base_structure_type(EStructureType.Object)

	def process_data(self, data_description):
		return super().process_data(data_description)

	def validate_substructure(self, data_description, struct_instance):
		return super().validate_substructure(data_description, struct_instance)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class GeometryObjectStructure(ObjectStructure):
	def __init__(self):
		super().__init__(EStructureType.GeometryObject)
		self.visible_flag = True
		self.shadow_flag = True
		self.motion_blur_flag = True
		self.mesh_map = dict()
		self.morph_map = dict()

	def validate_property(self, data_description, identifier):
		if identifier == "visible":
			return True, Data.EDataType.Bool

		if identifier == "shadow":
			return True, Data.EDataType.Bool

		if identifier == "motion_blur":
			return True, Data.EDataType.Bool

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "visible":
			self.visible_flag = data_value
			return True

		if identifier == "shadow":
			self.shadow_flag = data_value
			return True

		if identifier == "motion_blur":
			self.motion_blur_flag = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.type
		if local_type == EStructureType.Mesh or local_type == EStructureType.Morph:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		mesh_count = 0
		skin_count = 0

		struct_instance = self.first_sub_node
		while struct_instance:
			local_type = struct_instance.type
			if local_type == EStructureType.Mesh:
				key = struct_instance.mesh_level
				if key in self.mesh_map.keys():
					return EDataResult.DuplicateLod

				self.mesh_map[key] = struct_instance
				mesh_count += 1
				if struct_instance.skin_struct:
					skin_count += 1
			elif local_type == EStructureType.Morph:
				key = struct_instance.morph_index
				if key in self.morph_map.keys():
					return EDataResult.DuplicateMorph

				self.morph_map[key] = struct_instance

			struct_instance = struct_instance.next_node

		if mesh_count == 0:
			return OpenDDL.EDataResult.MissingSubstructure

		if skin_count != 0 and skin_count != mesh_count:
			return EDataResult.MissingLodSkin

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class LightObjectStructure(ObjectStructure):
	def __init__(self):
		super().__init__(EStructureType.LightObject)
		self.shadow_flag = True
		self.type_string = ""
		self.color = None
		self.intensity = 0.0
		self.illuminance = 0.0
		self.radius = 0.0
		self.angle = 0.0
		self.textures = []
		self.attenuations = []

	def validate_property(self, data_description, identifier):
		if identifier == "type":
			return True, Data.EDataType.String
	
		if identifier == "shadow":
			return True, Data.EDataType.Bool
	
		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "type":
			self.type_string = data_value
			return True

		if identifier == "shadow":
			self.shadow_flag = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.base_type == EStructureType.Attrib or struct_instance.type == EStructureType.Atten:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		if self.type_string == "infinite":
			# @Todo Prepare to handle infinite light here.
			x = 0
		elif self.type_string == "point":
			# @Todo Prepare to handle point light here.
			x = 0
		elif self.type_string == "spot":
			# @Todo Prepare to handle spot light here.
			x = 0
		else:
			return EDataResult.UndefinedLightType

		struct_instance = self.first_sub_node
		while struct_instance:
			local_type = struct_instance.type
			if local_type == EStructureType.Color:
				if struct_instance.attrib_string == "light":
					self.color = struct_instance.color

			elif local_type == EStructureType.Param:
				if struct_instance.attrib_string == "intensity":
					self.intensity = struct_instance.param

				elif struct_instance.attrib_string == "illuminance":
					self.illuminance = struct_instance.param

				elif struct_instance.attrib_string == "radius":
					self.radius = struct_instance.param

				elif struct_instance.attrib_string == "angle":
					self.angle = struct_instance.param

			elif local_type == EStructureType.Texture:
				# @NOTE Not very clean, we're pushing the handling to import time
				# Ideally this would be handled here, but we need an auxiliary texture
				# structure.
				self.textures.append(struct_instance)

				if struct_instance.attrib_string == "projection":
					local_texture_name = struct_instance.texture_name
					# Process light texture here.

			elif local_type == EStructureType.Atten:
				# @NOTE Not very clean, we're pushing the handling to import time
				# Ideally this would be handled here, but we need an auxiliary attenuation
				# structure.
				self.attenuations.append(struct_instance)

				local_atten_kind = struct_instance.atten_kind
				local_curve_type = struct_instance.curve_type

				if local_atten_kind == "distance":
					if local_curve_type == "linear" or local_curve_type == "smooth":
						local_begin_param = struct_instance.begin_param
						local_end_param = struct_instance.end_param
						# Process linear or smooth attenuation here.

					elif local_curve_type == "inverse":
						local_scale_param = struct_instance.scale_param
						local_linear_param = struct_instance.linear_param
						# Process inverse attenuation here.

					elif local_curve_type == "inverse_square":
						local_scale_param = struct_instance.scale_param
						local_quadratic_param = struct_instance.quadratic_param
						# Process inverse square attenuation here.

					else:
						return EDataResult.UndefinedCurve
				elif local_atten_kind == "angle":
					local_end_param = struct_instance.end_param
					# Process angular attenuation here.

				elif local_atten_kind == "cos_angle":
					local_end_param = struct_instance.end_param
					# Process angular attenuation here.

				else:
					return EDataResult.UndefinedAtten

			struct_instance = struct_instance.next_node

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class CameraObjectStructure(ObjectStructure):
	def __init__(self):
		super().__init__(EStructureType.CameraObject)
		self.projection_distance = 0.0
		self.near_depth = 0.0
		self.far_depth = 0.0

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.Param:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		self.projection_distance = 1.0
		self.near_depth = 0.1
		self.far_depth = 1000.0

		distance_scale = data_description.distance_scale
		angle_scale = data_description.angle_scale

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == EStructureType.Param:
				attrib_string = struct_instance.attrib_string
				param = struct_instance.param

				if attrib_string == "fovy":
					t = math.tan(param * angle_scale * 0.5)
					if t > sys.float_info.min:
						self.projection_distance = 1.0 / t

				elif attrib_string == "near":
					if param > sys.float_info.min:
						self.near_depth = param * distance_scale

				elif attrib_string == "far":
					if param > sys.float_info.min:
						self.far_depth = param * distance_scale

			struct_instance = struct_instance.next_node

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class GeometryNodeStructure(NodeStructure):
	def __init__(self):
		super().__init__(EStructureType.GeometryNode)
		# The first entry in each of the following arrays indicates whether the flag
		# is specified by a property. If true, then the second entry in the array
		# indicates the actual value that the property specified.
		self.visible_flag = [False, True]
		self.shadow_flag = [False, True]
		self.motion_blur_flag = [False, True]

		self.geometry_object_struct = GeometryObjectStructure()
		self.material_struct_array = []
		self.morph_wieght_list = []

	def validate_property(self, data_description, identifier):
		if identifier == "visible":
			return True, Data.EDataType.Bool
		
		if identifier == "shadow":
			return True, Data.EDataType.Bool
		
		if identifier == "motion_blur":
			return True, Data.EDataType.Bool

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "visible":
			self.visible_flag[1] = data_value
			self.visible_flag[0] = True
			return True

		if identifier == "shadow":
			self.shadow_flag[1] = data_value
			self.shadow_flag[0] = True
			return True

		if identifier == "motion_blur":
			self.motion_blur_flag[1] = data_value
			self.motion_blur_flag[0] = True
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.type
		if local_type == EStructureType.ObjectRef or local_type == EStructureType.MaterialRef or local_type == EStructureType.MorphWeight:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		object_flag = False
		material_flag = [False] * 256
		max_material_index = -1

		struct_instance = self.first_sub_node
		while struct_instance:
			local_type = struct_instance.type
			if local_type == EStructureType.ObjectRef:
				if object_flag:
					return OpenDDL.EDataResult.ExtraneousSubstructure

				object_flag = True

				object_struct = struct_instance.target_struct
				if object_struct.type != EStructureType.GeometryObject:
					return EDataResult.InvalidObjectRef

				self.geometry_object_struct = object_struct
			
			elif local_type == EStructureType.MaterialRef:
				index = struct_instance.material_index
				if index > 255:
					# We only support up to 256 materials.
					return EDataResult.MaterialIndexUnsupported

				if material_flag[index]:
					return EDataResult.DuplicateMaterialRef

				material_flag[index] = True
				max_material_index = max(max_material_index, index)
			
			elif local_type == EStructureType.MorphWeight:
				self.morph_wieght_list.append(struct_instance)

			struct_instance = struct_instance.next_node

		if object_flag == False:
			return OpenDDL.EDataResult.MissingSubstructure

		if max_material_index >= 0:
			self.material_struct_array = [None] * (max_material_index + 1)
			a = 0
			while a < max_material_index:
				if material_flag[a] == False:
					return EDataResult.MissingMaterialRef
				a += 1

			struct_instance = self.first_sub_node
			while struct_instance:
				if struct_instance.type == EStructureType.MaterialRef:
					self.material_struct_array[struct_instance.material_index] = struct_instance.target_struct

				struct_instance = struct_instance.next_node

		return Data.EDataResult.Okay

	def get_object_structure(self):
		return self.geometry_object_struct

	def find_morph_weight_structure(self, index):
		for morph_struct in self.morph_wieght_list:
			if morph_struct.morph_index == index:
				return morph_struct

		return None

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class NameStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Name)
		self.name = ""

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.String:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(struct_instance.data_array) != 1:
			return OpenDDL.EDataResult.InvalidDataFormat

		self.name = struct_instance.data_array[0]
		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class LightNodeStructure(NodeStructure):
	def __init__(self):
		super().__init__()
		self.type = EStructureType.LightNode
		# The first entry in each of the following arrays indicates whether the flag
		# is specified by a property. If true, then the second entry in the array
		# indicates the actual value that the property specified.
		self.shadow_flag = [False, True]
		self.light_object_structure = None

	def validate_property(self, data_description, identifier):
		if identifier == "shadow":
			return True, Data.EDataType.Bool

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "shadow":
			self.shadow_flag[1] = data_value
			self.shadow_flag[0] = True
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.ObjectRef:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		object_flag = False

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == EStructureType.ObjectRef:
				if object_flag:
					return OpenDDL.EDataResult.ExtraneousSubstructure

				object_flag = True

				object_struct = struct_instance.target_struct
				if object_struct.type != EStructureType.LightObject:
					return EDataResult.InvalidObjectRef

				self.light_object_structure = object_struct
			
			struct_instance = struct_instance.next_node


		if object_flag == False:
			return OpenDDL.EDataResult.MissingSubstructure

		return Data.EDataResult.Okay

	def get_object_structure(self):
		return self.light_object_structure

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class CameraNodeStructure(NodeStructure):
	def __init__(self):
		super().__init__()
		self.type = EStructureType.CameraNode
		self.camera_object_structure = None

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.ObjectRef:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		object_flag = False

		struct_instance = self.first_sub_node
		while struct_instance:
			if struct_instance.type == EStructureType.ObjectRef:
				if object_flag:
					return OpenDDL.EDataResult.ExtraneousSubstructure

				object_flag = True

				object_struct = struct_instance.target_struct
				if object_struct.type != EStructureType.CameraObject:
					return EDataResult.InvalidObjectRef

				self.camera_object_structure = object_struct
			
			struct_instance = struct_instance.next_node

		if object_flag == False:
			return OpenDDL.EDataResult.MissingSubstructure

		return Data.EDataResult.Okay

	def get_object_structure(self):
		return self.camera_object_structure

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class VertexArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.VertexArray)
		self.attrib_string = ""
		self.attrib_index = 0
		self.morph_index = 0
		self.vertex_count = 0
		self.component_count = 0
		self.array_storage = []
		self.float_storage = []
		self.vertex_array_data = []

	def validate_property(self, data_description, identifier):
		if identifier == "attrib":
			return True, Data.EDataType.String

		if identifier == "index":
			return True, Data.EDataType.UInt32

		if identifier == "morph":
			return True, Data.EDataType.UInt32

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "attrib":
			self.attrib_string = data_value
			return True

		if identifier == "index":
			self.attrib_index = data_value
			return True

		if identifier == "morph":
			self.morph_index = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		local_type = struct_instance.type
		if local_type == Data.EDataType.Half or local_type == Data.EDataType.Float or local_type == Data.EDataType.Double:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		element_count = 0
		data = None

		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		local_type = struct_instance.type
		element_count = len(struct_instance.data_array)
		if local_type == Data.EDataType.Float:
			# Whole copy :( ???
			data = struct_instance.data_array
		
		elif local_type == Data.EDataType.Float:
			for double_element in struct_instance.data_array:
				self.float_storage.append(float(double_element))

			# Whole copy :( ???
			data = self.float_storage

		else: # Must be Half
			# @TODO We don't really support Half
			for double_element in struct_instance.data_array:
				self.float_storage.append(float(double_element))

			# Whole copy :( ???
			data = self.float_storage

		array_size = struct_instance.array_size
		self.vertex_count = element_count / array_size
		self.component_count = array_size
		# Whole copy :(
		self.array_storage = data

		if self.attrib_string == "position":
			if array_size == 3:
				scale = data_description.distance_scale
				up = data_description.up_direction[0]
				
				# Apply scale if necessary.
				if scale != 1.0 or up != 'z':
					transform = None
					if up == 'z':
						transform = Matrix4D()
						transform.set_most(scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0)
					else:
						transform = Matrix4D()
						transform.set_most(scale, 0.0, 0.0, 0.0, 0.0, 0.0, -scale, 0.0,	0.0, scale, 0.0, 0.0)

					a = 0
					while a < element_count:
						transformed_vertex = VMath.mulMatrix4DVector3D(transform, Vector3D(data[a], data[a + 1], data[a + 2]))
						self.vertex_array_data.append([transformed_vertex.x, transformed_vertex.y, transformed_vertex.z])
						a += 3
				# Otherwise just save vertices normally.
				else:
					a = 0
					while a < element_count:
						self.vertex_array_data.append([data[a], data[a + 1], data[a + 2]])
						a += 3

		elif self.attrib_string == "normal" or self.attrib_string == "tangent" or self.attrib_string == "bitangent":
			if array_size == 3:
				a = 0
				if data_description.up_direction[0] != 'z':
					while a < element_count:
						self.vertex_array_data.append([data[a], -1.0 * data[a + 2], data[a + 1]])
						a += 3
				else:
					while a < element_count:
						self.vertex_array_data.append([data[a], data[a + 1], data[a + 2]])
						a += 3

		elif self.attrib_string == "color":
			if array_size == 3:
				a = 0
				while a < element_count:
					color = Vector3D(data[a], data[a + 1], data[a + 2])
					color = data_description.convert_color(color)
					self.vertex_array_data.append([color.x, color.y, color.z])
					a += 3
			elif array_size == 4:
				a = 0
				while a < element_count:
					color = Vector3D(data[a], data[a + 1], data[a + 2])
					color = data_description.convert_color(color)
					self.vertex_array_data.append([color.x, color.y, color.z, data[a + 3]])
					a += 4
		
		elif self.attrib_string == "texcoord":
			if array_size == 2:
				a = 0
				while a < element_count:
					self.vertex_array_data.append([data[a], data[a + 1]])
					a += 2

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class IndexArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.IndexArray)
		self.material_index = 0
		self.restart_index = 0
		self.front_face = "ccw"
		self.element_count = 0
		self.index_array_data = []
		self.array_storage = [] # Same as index_array_data but not organized by triangles. Raw data.

	def validate_property(self, data_description, identifier):
		if identifier == "material":
			return True, Data.EDataType.UInt32

		if identifier == "restart":
			return True, Data.EDataType.UInt64

		if identifier == "front":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "material":
			self.material_index = data_value
			return True

		if identifier == "restart":
			self.restart_index = data_value
			return True

		if identifier == "front":
			self.front_face = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == Data.EDataType.UInt8 or type == Data.EDataType.UInt16 or type == Data.EDataType.UInt32 or type == Data.EDataType.UInt64:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if struct_instance.array_size != 3:
			return OpenDDL.EDataResult.InvalidDataFormat
		
		# Do something with the index array here.
		type = struct_instance.type
		if type == Data.EDataType.UInt32:
			self.element_count = len(struct_instance.data_array) # Should divide by 3?
			self.array_storage = struct_instance.data_array

			a = 0
			face = []
			for index in struct_instance.data_array:
				face.append(index)
				a += 1
				if a == 3:
					self.index_array_data.append(face)
					face = []
					a = 0
		else:
			return OpenDDL.EDataResult.InvalidDataFormat

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class BoneRefArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.BoneRefArray)
		self.bone_count = 0
		self.bone_node_array = []

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Ref:
			return True
		
		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.bone_count = len(struct_instance.data_array)

		if self.bone_count != 0:
			self.bone_node_array = [None] * self.bone_count

			a = 0
			while a < self.bone_count:
				reference = struct_instance.data_array[a]
				bone_structure = data_description.find_structure(reference)

				if not bone_structure:
					return OpenDDL.EDataResult.BrokenRef

				if bone_structure.type != EStructureType.BoneNode:
					return EDataResult.InvalidBoneRef

				self.bone_node_array[a] = bone_structure
				a += 1
		
		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class BoneCountArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.BoneCountArray)
		self.vertex_count = 0
		self.bone_count_array = []
		self.array_storage = []

	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == Data.EDataType.UInt8 or type == Data.EDataType.UInt16 or type == Data.EDataType.UInt32 or type == Data.EDataType.UInt64:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if struct_instance.array_size != 0:
			return OpenDDL.EDataResult.InvalidDataFormat

		type = struct_instance.type
		if type == Data.EDataType.UInt16:
			self.vertex_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_count_array = struct_instance.data_array
			self.array_storage = struct_instance.data_array
			
		elif type == Data.EDataType.UInt8:
			self.vertex_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_count_array = struct_instance.data_array
			self.array_storage = struct_instance.data_array
		
		elif type == Data.EDataType.UInt32:
			self.vertex_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_count_array = struct_instance.data_array
			self.array_storage = [0] * self.vertex_count
			a = 0
			while a < self.vertex_count:
				index = struct_instance.data_array[a]
				if index > 65535:
					# We only support 16-bit indexes or smaller.
					return EDataResult.IndexValueUnsupported
				self.array_storage[a] = index
				a += 1
		
		else: # must be 64-bit.
			self.vertex_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_count_array = struct_instance.data_array
			self.array_storage = [0] * self.vertex_count
			a = 0
			while a < self.vertex_count:
				index = struct_instance.data_array[a]
				if index > 65535:
					# We only support 16-bit indexes or smaller.
					return EDataResult.IndexValueUnsupported
				self.array_storage[a] = index
				a += 1
		
		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class BoneIndexArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.BoneIndexArray)
		self.bone_index_count = 0
		self.bone_index_array = []
		self.array_storage = []

	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == Data.EDataType.UInt8 or type == Data.EDataType.UInt16 or type == Data.EDataType.UInt32 or type == Data.EDataType.UInt64:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if struct_instance.array_size != 0:
			return OpenDDL.EDataResult.InvalidDataFormat

		type = struct_instance.type
		if type == Data.EDataType.UInt16:
			self.bone_index_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_index_array = struct_instance.data_array
			
		elif type == Data.EDataType.UInt8:
			self.bone_index_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_index_array = struct_instance.data_array
			self.array_storage = [0] * self.bone_index_count
			a = 0
			while a < self.bone_index_count:
				self.array_storage[a] = struct_instance.data_array[a]
				a += 1
		
		elif type == Data.EDataType.UInt32:
			self.bone_index_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_index_array = struct_instance.data_array
			self.array_storage = [0] * self.bone_index_count
			a = 0
			while a < self.bone_index_count:
				index = struct_instance.data_array[a]
				if index > 65535:
					# We only support 16-bit indexes or smaller.
					return EDataResult.IndexValueUnsupported
				self.array_storage[a] = index
				a += 1
		
		else: # must be 64-bit.
			self.bone_index_count = len(struct_instance.data_array)
			# Full copy :( Suppose to just be a pointer
			# This needs to be refactored when we support actual
			# arrays in python
			self.bone_index_array = struct_instance.data_array
			self.array_storage = [0] * self.bone_index_count
			a = 0
			while a < self.bone_index_count:
				index = struct_instance.data_array[a]
				if index > 65535:
					# We only support 16-bit indexes or smaller.
					return EDataResult.IndexValueUnsupported
				self.array_storage[a] = index
				a += 1
		
		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class BoneWeightArrayStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.BoneWeightArray)
		self.bone_weight_count = 0
		self.bone_weight_array = []

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if struct_instance.array_size != 0:
			return OpenDDL.EDataResult.InvalidDataFormat

		self.bone_weight_count = len(struct_instance.data_array)
		# Full copy :(
		self.bone_weight_array = struct_instance.data_array

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class SkeletonStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Skeleton)
		self.bone_ref_array_structure = None
		self.transform_structure = None
		
	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == EStructureType.BoneRefArray or type == EStructureType.Transform:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		structure = self.get_first_substructure(EStructureType.BoneRefArray)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.BoneRefArray) != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.bone_ref_array_structure = structure

		structure = self.get_first_substructure(EStructureType.Transform)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.Transform) != structure:
			return OpenDDL.EDataResult.MissingSubstructure

		self.transform_structure = structure
		
		if self.bone_ref_array_structure.bone_count != len(self.transform_structure.transform_array):
			return EDataResult.BoneCountMismatch

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class SkinStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Skin)
		self.skin_transform = Matrix4D()
		self.skeleton_structure = None
		self.bone_count_array_structure = None
		self.bone_index_array_structure = None
		self.bone_weight_array_structure = None

	def validate_substructure(self, data_description, struct_instance):
		type = struct_instance.type
		if type == EStructureType.Transform or type == EStructureType.Skeleton or type == EStructureType.BoneCountArray or type == EStructureType.BoneIndexArray or type == EStructureType.BoneWeightArray:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		structure = self.get_first_substructure(EStructureType.Transform)
		if structure:
			if self.get_last_substructure(EStructureType.Transform) != structure:
				return OpenDDL.EDataResult.ExtraneousSubstructure

			self.skin_transform = structure.transform_array[0]
			data_description.adjust_transform(self.skin_transform)
		else:
			self.skin_transform.set_identity()

		structure = self.get_first_substructure(EStructureType.Skeleton)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.Skeleton) != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.skeleton_structure = structure

		structure = self.get_first_substructure(EStructureType.BoneCountArray)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.BoneCountArray) != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.bone_count_array_structure = structure

		structure = self.get_first_substructure(EStructureType.BoneIndexArray)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.BoneIndexArray) != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.bone_index_array_structure = structure

		structure = self.get_first_substructure(EStructureType.BoneWeightArray)
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.get_last_substructure(EStructureType.BoneWeightArray) != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.bone_weight_array_structure = structure

		bone_index_count = self.bone_index_array_structure.bone_index_count
		if self.bone_weight_array_structure.bone_weight_count != bone_index_count:
			return EDataResult.BoneWeightCountMismatch

		vertex_count = self.bone_count_array_structure.vertex_count
		bone_weight_count = 0
		a = 0
		while a < vertex_count:
			count = self.bone_count_array_structure.bone_count_array[a]
			bone_weight_count += count
			a += 1

		if bone_weight_count != bone_index_count:
			return EDataResult.BoneWeightCountMismatch

		# Do applicatoin-specific skin processing here

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MorphStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Morph)
		self.morph_index = 0
		self.base_index = 0
		self.morphe_name = ""
		# The value of baseFlag indicates whether the base property was 
		# actually specified for the structure.
		self.base_flag = False

	def validate_property(self, data_description, identifier):
		if identifier == "index":
			return True, Data.EDataType.UInt32

		if identifier == "base":
			return True, Data.EDataType.UInt32

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "index":
			self.morph_index = data_value
			return True
		
		if identifier == "base":
			self.base_index = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == EStructureType.Name:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		result = super().process_data(data_description)
		if result != Data.EDataResult.Okay:
			return result

		self.morph_name = ""
		structure = self.first_sub_node
		if not structure:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != structure:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		self.morph_name = structure.name

		# Do application-specific morph processing here.

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ObjectRefStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.ObjectRef)
		self.target_struct = None

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Ref:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(struct_instance.data_array) != 0:
			object_struct = data_description.find_structure(struct_instance.data_array[0])
			if object_struct:
				self.target_struct = object_struct
				return Data.EDataResult.Okay

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MaterialRefStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.MaterialRef)
		self.material_index = 0
		self.target_struct = None

	def validate_property(self, data_description, identifier):
		if identifier == "index":
			return True, Data.EDataType.UInt32

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "index":
			self.material_index = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Ref:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(struct_instance.data_array) != 0:
			material_struct = data_description.find_structure(struct_instance.data_array[0])
			if material_struct:
				if material_struct.type != EStructureType.Material:
					return EDataResult.InvalidMaterialRef

				self.target_struct = material_struct
				return Data.EDataResult.Okay

		return OpenDDL.EDataResult.BrokenRef

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class AnimatableStructure(OpenGexStructure):
	def __init__(self, in_type):
		super().__init__(in_type)

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MatrixStructure(AnimatableStructure):
	def __init__(self, in_type):
		super().__init__(in_type)
		self.set_base_structure_type(EStructureType.Matrix)
		self.object_flag = False
		self.matrix_value = Matrix4D()
		self.matrix_value.set_identity()

	def validate_property(self, data_description, identifier):
		if identifier == "object":
			return True, Data.EDataType.Bool

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "object":
			self.object_flag = data_value
			return True

		return False

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class TransformStructure(MatrixStructure):
	def __init__(self):
		super().__init__(EStructureType.Transform)
		self.transform_array = []

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			array_size = struct_instance.array_size
			return (array_size == 16) or (array_size == 12) or (array_size == 9) or (array_size == 6) or (array_size == 4)

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		array_size = struct_instance.array_size
		transform_count = len(struct_instance.data_array) / array_size
		if transform_count == 0:
			return OpenDDL.EDataResult.InvalidDataFormat

		data = struct_instance.data_array # Copy :(

		if array_size == 16:
			a = 0
			t = 0
			while t < transform_count:
				transform = Matrix4D()
				transform.set_all(data[a], data[a + 1], data[a + 2], data[a + 3], data[a + 4], data[a + 5], data[a + 6], data[a + 7], data[a + 8], data[a + 9], data[a + 10], data[a + 11], data[a + 12], data[a + 13], data[a + 14], data[a + 15])
				self.transform_array.append(transform)
				t += 1
				a += 16
		elif array_size == 12:
			a = 0
			t = 0
			while t < transform_count:
				transform = Matrix4D()
				transform.set_most(data[a], data[a + 3], data[a + 6], data[a + 9], data[a + 1], data[a + 4], data[a + 7], data[a + 10], data[a + 2], data[a + 5], data[a + 8], data[a + 11])
				self.transform_array.append(transform)
				t += 1
				a += 12
		elif array_size == 9:
			a = 0
			t = 0
			while t < transform_count:
				transform = Matrix4D()
				transform.set_most(data[a], data[a + 3], data[a + 6], 0.0, data[a + 1], data[a + 4], data[a + 7], 0.0, data[a + 2], data[a + 5], data[a + 8], 0.0)
				self.transform_array.append(transform)
				t += 1
				a += 9
		elif array_size == 6:
			a = 0
			t = 0
			while t < transform_count:
				transform = Matrix4D()
				transform.set_most(data[a], data[a + 2], 0.0, data[a + 4], data[a + 1], data[a + 3], 0.0, data[a + 5], 0.0, 0.0, 1.0, 0.0)
				self.transform_array.append(transform)
				t += 1
				a += 6
		else:
			a = 0
			t = 0
			while t < transform_count:
				transform = Matrix4D()
				transform.set_most(data[a], data[a + 2], 0.0, 0.0, data[a + 1], data[a + 3], 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
				self.transform_array.append(transform)
				t += 1
				a += 4

		self.matrix_value = self.transform_array[0]
		return Data.EDataResult.Okay

	def update_animation(self, data_description, data):
		data_size = len(data)
		a = 0
		while a < data_size:
			self.matrix_value.set_all(data[a], data[a + 1], data[a + 2], data[a + 3], data[a + 4], data[a + 5], data[a + 6], data[a + 7], data[a + 8], data[a + 8], data[a + 9], data[a + 10], data[a + 11], data[a + 12], data[a + 13], data[a + 14], data[a + 15])
			a += 16

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class TranslationStructure(MatrixStructure):
	def __init__(self):
		super().__init__(EStructureType.Translation)
		self.translation_kind = "xyz"

	def validate_property(self, data_description, identifier):
		if identifier == "kind":
			return True, Data.EDataType.String
		
		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "kind":
			self.translation_kind = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			array_size = struct_instance.array_size
			return array_size == 0 or array_size == 3

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		array_size = struct_instance.array_size

		if self.translation_kind == "x" or self.translation_kind == "y" or self.translation_kind == "z":
			if array_size != 0 or len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

		elif self.translation_kind == "xyz":
			if array_size != 3 or len(struct_instance.data_array) != 3:
				return OpenDDL.EDataResult.InvalidDataFormat
		
		else:
			return EDataResult.InvalidTranslationKind

		self.update_animation(data_description, struct_instance.data_array)
		return Data.EDataResult.Okay

	def update_animation(self, data_description, data):
		if self.translation_kind == "x":
			self.matrix_value.set_translation(data[0], 0.0, 0.0)
		elif self.translation_kind == "y":
			self.matrix_value.set_translation(0.0, data[0], 0.0)
		elif self.translation_kind == "z":
			self.matrix_value.set_translation(0.0, 0.0, data[0])
		else:
			self.matrix_value.set_translation(data[0], data[1], data[2])

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------    

class RotationStructure(MatrixStructure):
	def __init__(self):
		super().__init__(EStructureType.Rotation)
		self.rotation_kind = "axis"

	def validate_property(self, data_description, identifier):
		if identifier == "kind":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "kind":
			self.rotation_kind = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			array_size = struct_instance.arra_size
			return array_size == 0 or array_size == 4

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		array_size = struct_instance.array_size

		if self.rotation_kind == "x" or self.rotation_kind == "y" or self.rotation_kind == "z":
			if array_size != 0 or len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidFormat
		elif self.rotation_kind == "axis" or self.rotation_kind == "quaternion":
			if array_size != 4 or len(struct_instance.data_array) != 4:
				return OpenDDL.EDataResult.InvalidFormat
		else:
			return EDataResult.InvalidRotationKind

		self.update_animation(data_description, struct_instance.data_array)
		return Data.EDataResult.Okay

	def update_animation(self, data_description, data):
		scale = data_description.scale

		if self.rotation_kind == "x":
			self.matrix_value.set_rotation(data[0] * scale, Vector3D(1.0, 0.0, 0.0))
		elif self.rotation_kind == "y":
			self.matrix_value.set_rotation(data[0] * scale, Vector3D(0.0, 1.0, 0.0))
		elif self.rotation_kind == "z":
			self.matrix_value.set_rotation(data[0] * scale, Vector3D(0.0, 0.0, 1.0))
		elif self.rotation_kind == "axix":
			self.matrix_value.set_rotation(data[0] * scale, Vector3D(data[1], data[2], data[3]))
		else:
			self.matrix_value.set_rotation(Qtrn(data[0], data[1], data[2], data[3]))
			
# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class ScaleStructure(MatrixStructure):
	def __init__(self):
		super().__init__(EStructureType.Scale)
		self.rotation_kind = "xyz"

	def validate_property(self, data_description, identifier):
		if identifier == "kind":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "kind":
			self.scale_kind = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			array_size = struct_instance.array_size
			return array_size == 0 or array_size == 3

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		array_size = struct_instance.array_size

		if self.scale_kind == "x" or self.scale_kind == "y" or self.scale_kind == "z":
			if array_size != 0 or len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat
		elif self.scale_kind == "xyz":
			if array_size != 3 or len(struct_instance.data_array) != 3:
				return OpenDDL.EDataResult.InvalidDataFormat
		else:
			return EDataResult.InvalidScaleKind

		self.update_animation(data_description, struct_instance.data_array)
		return Data.EDataResult.Okay

	def update_animation(self, data_description, data):
		if self.scale_kind == "x":
			self.matrix_value.set_scale(data[0], 0.0, 0.0)
		elif self.scale_kind == "y":
			self.matrix_value.set_scale(0.0, data[0], 0.0)
		elif self.scale_kind == "z":
			self.matrix_value.set_scale(0.0, 0.0, data[0])
		elif self.scale_kind == "xyz":
			self.matrix_value.set_scale(data[0], data[1], data[2])

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MorphWeightStructure(AnimatableStructure):
	def __init__(self):
		super().__init__(EStructureType.MorpheWeight)
		self.morph_index = 0
		self.morphe_weight = 0.0

	def validate_property(self, data_description, identifier):
		if identifier == "index":
			return True, Data.EDataType.kUInt32

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "index":
			self.morph_index = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		if struct_instance.type == Data.EDataType.Float:
			return struct_instance.array_size == 0

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if len(struct_instance.data_array) == 1:
			self.morph_weight = struct_instance.data_array[0]
		else:
			return OpenDDL.EDataResult.InvalidDataFormat

		# Do application-specific morph weight processing here.

		return Data.EDataResult.Okay

	def update_animation(self, data_description, data):
		self.morph_weight = data[0]

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class MetricStructure(OpenGexStructure):
	def __init__(self):
		super().__init__(EStructureType.Metric)
		self.metricKey = ""

	def validate_property(self, data_description, identifier):
		if identifier == "key":
			return True, Data.EDataType.String

		return False

	def set_property(self, data_description, identifier, data_value):
		if identifier == "key":
			self.metricKey = data_value
			return True

		return False

	def validate_substructure(self, data_description, struct_instance):
		struct_type = struct_instance.type
		if struct_type == Data.EDataType.Float or struct_type == Data.EDataType.String:
			return True

		return super().validate_substructure(data_description, struct_instance)

	def process_data(self, data_description):
		struct_instance = self.first_sub_node
		if not struct_instance:
			return OpenDDL.EDataResult.MissingSubstructure

		if self.last_sub_node != struct_instance:
			return OpenDDL.EDataResult.ExtraneousSubstructure

		if self.metricKey == "distance":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			# DataStructure
			if len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.distance_scale = struct_instance.data_array[0]
		elif self.metricKey == "angle":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			# DataStructure
			if len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.angle_scale = struct_instance.data_array[0]
		elif self.metricKey == "time":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			# DataStructure
			if len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.time_scale = struct_instance.data_array[0]
		elif self.metricKey == "up":
			if struct_instance.type != Data.EDataType.String:
				return OpenDDL.EDataResult.InvalidDataFormat

			# DataStructure
			if len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

			string = struct_instance.data_array[0]
			if string != "z" and string != "y":
				return EDataResult.InvalidUpDirection

			data_description.up_direction = string
		elif self.metricKey == "forward":
			if struct_instance.type != Data.EDataType.String:
				return OpenDDL.EDataResult.InvalidDataFormat

			# DataStructure
			if len(struct_instance.data_array) != 1:
				return OpenDDL.EDataResult.InvalidDataFormat

			string = struct_instance.data_array[0]
			if string != "x" and string != "y" and string != "z" and string != "-x" and string != "-y" and string != "-z":
				return EDataResult.InvalidForwardDirection

			data_description.forward_direction = string
		elif self.metricKey == "red":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			if struct_instance.array_size != 2 or len(struct_instance.data_array) != 2:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.red_chromaticity = Vector2D(struct_instance.data_array[0], struct_instance.data_array[1])
		elif self.metricKey == "green":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			if struct_instance.array_size != 2 or len(struct_instance.data_array) != 2:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.green_chromaticity = Vector2D(struct_instance.data_array[0], struct_instance.data_array[1])
		elif self.metricKey == "blue":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			if struct_instance.array_size != 2 or len(struct_instance.data_array) != 2:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.blue_chromaticity = Vector2D(struct_instance.data_array[0], struct_instance.data_array[1])
		elif self.metricKey == "white":
			if struct_instance.type != Data.EDataType.Float:
				return OpenDDL.EDataResult.InvalidDataFormat

			if struct_instance.array_size != 2 or len(struct_instance.data_array) != 2:
				return OpenDDL.EDataResult.InvalidDataFormat

			data_description.white_chromaticity = Vector2D(struct_instance.data_array[0], struct_instance.data_array[1])

		return Data.EDataResult.Okay

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

class OpenGexDataDescription(OpenDDL.DataDescription):
	def __init__(self):
		super().__init__()
		self.distance_scale = 1.0
		self.angle_scale = 1.0
		self.time_scale = 1.0
		self.up_direction = "z"
		self.forward_direction = "x"
		self.red_chromaticity = Vector2D(0.64, 0.33)
		self.green_chromaticity = Vector2D(0.3, 0.6)
		self.blue_chromaticity = Vector2D(0.15, 0.06)
		self.white_chromaticity = Vector2D(0.3127, 0.329)
		self.color_init_flag = True
		self.color_matrix = Matrix3D()
		self.animation_list = []

	def create_structure(self, identifier):
		if identifier == "Metric":
			return MetricStructure()
		
		if identifier == "Name":
			return NameStructure()
		
		if identifier == "ObjectRef":
			return ObjectRefStructure()
		
		if identifier == "MaterialRef":
			return MaterialRefStructure()
		
		if identifier == "Transform":
			return TransformStructure()
		
		if identifier == "Translation":
			return TranslationStructure()
		
		if identifier == "Rotation":
			return RotationStructure()
		
		if identifier == "Scale":
			return ScaleStructure()
		
		if identifier == "MorphWeight":
			return MorphWeightStructure()
		
		if identifier == "Node":
			return NodeStructure()
		
		if identifier == "BoneNode":
			return BoneNodeStructure()
		
		if identifier == "GeometryNode":
			return GeometryNodeStructure()
		
		if identifier == "LightNode":
			return LightNodeStructure()
		
		if identifier == "CameraNode":
			return CameraNodeStructure()
		
		if identifier == "VertexArray":
			return VertexArrayStructure()
		
		if identifier == "IndexArray":
			return IndexArrayStructure()
		
		if identifier == "BoneRefArray":
			return BoneRefArrayStructure()
		
		if identifier == "BoneCountArray":
			return BoneCountArrayStructure()
		
		if identifier == "BoneIndexArray":
			return BoneIndexArrayStructure()
		
		if identifier == "BoneWeightArray":
			return BoneWeightArrayStructure()
		
		if identifier == "Skeleton":
			return SkeletonStructure()
		
		if identifier == "Skin":
			return SkinStructure()
		
		if identifier == "Morph":
			return MorphStructure()
		
		if identifier == "Mesh":
			return MeshStructure()
		
		if identifier == "GeometryObject":
			return GeometryObjectStructure()
		
		if identifier == "LightObject":
			return LightObjectStructure()
		
		if identifier == "CameraObject":
			return CameraObjectStructure()
		
		if identifier == "Param":
			return ParamStructure()
		
		if identifier == "Color":
			return ColorStructure()
		
		if identifier == "Spectrum":
			return SpectrumStructure()
		
		if identifier == "Texture":
			return TextureStructure()
		
		if identifier == "Atten":
			return AttenStructure()
		
		if identifier == "Material":
			return MaterialStructure()
		
		if identifier == "Key":
			return KeyStructure()
		
		if identifier == "Time":
			return TimeStructure()
		
		if identifier == "Value":
			return ValueStructure()
		
		if identifier == "Track":
			return TrackStructure()
		
		if identifier == "Animation":
			return AnimationStructure()
		
		if identifier == "Clip":
			return ClipStructure()
		
		return None

	def process_data(self):
		self.color_init_flag = False
		
		result = super().process_data()
		if result == Data.EDataResult.Okay:
			struct_instance = self.root_structure.first_sub_node
			while struct_instance:
				if struct_instance.base_type == EStructureType.Node:
					struct_instance.update_node_transforms(self)
				
				struct_instance = struct_instance.next_node
		
		return result

	def adjust_transform(self, transform):
		adjusted = Matrix4D()
		adjusted.set(transform)
		adjusted.m03 = adjusted.m03 * self.distance_scale
		adjusted.m13 = adjusted.m13 * self.distance_scale
		adjusted.m23 = adjusted.m23 * self.distance_scale
		
		if self.up_direction[0] == "y":
			adjusted.set_all(adjusted.m00, -adjusted.m02,  adjusted.m01, adjusted.m03, -adjusted.m20,  adjusted.m22, -adjusted.m21, -adjusted.m23, adjusted.m10, -adjusted.m12,  adjusted.m11,  adjusted.m13)
	
		return adjusted

	def convert_color(self, color):
		if self.color_init_flag == False:
			self.color_init_flag = True
			
			xr = self.red_chromaticity.x
			xg = self.green_chromaticity.x
			xb = self.blue_chromaticity.x
			xw = self.white_chromaticity.x
			
			zr = 1.0 - xr - self.red_chromaticity.y
			zg = 1.0 - xg - self.green_chromaticity.y
			zb = 1.0 - xb - self.blue_chromaticity.y
			zw = 1.0 - xw - self.white_chromaticity.y
			
			iyr = 1.0 / self.red_chromaticity.y
			iyg = 1.0 / self.green_chromaticity.y
			iyb = 1.0 / self.blue_chromaticity.y
			iyw = 1.0 / self.white_chromaticity.y
			
			m = Matrix3D()
			m.set_all(xr * iyr, xg * iyg, xb * iyb, 1.0, 1.0, 1.0, zr * iyr, zg * iyg, zb * iyb)
			
			lum = VMath.mulMatrix3DVector3D(VMath.inverse_matrix3D(m), Vector3D(xw * iyw, 1.0, zw * iyw))
			m.m00 *= lum.x
			m.m01 *= lum.y
			m.m02 *= lum.z
		
			self.color_matrix.set_all(3.24097, -1.537383, -0.498611, -0.969244, 1.875968, 0.041555, 0.05563, -0.203977, 1.056972)
			self.color_matrix = self.color_matrix * m
		
		color = VMath.mulMatrix3DVector3D(self.color_matrix, color)
		return color

	def get_animation_time_range(self, clip):
		time_range = Range()
		animation_flag = False
		
		for node in self.animation_list:
			animation_structure = node.data
			if animation_structure.clip_index == clip:
				if animation_flag:
					range = animation_structure.get_animation_time_range()
					time_range.min = min(time_range.min, range.min)
					time_range.max = max(time_range.max, range.max)
				else:
					animation_flag = True
					time_range = animation_structure.get_animation_time_range()
		
		if animation_flag:
			time_range.min *= self.time_scale
			time_range.max *= self.time_scale
			return time_range
		
		return Range(0.0, 0.0)

	def update_animation(self, clip, time):
		time /= self.time_scale

		for node in self.animation_list:
			animation_structure = node.data
			if animation_structure.clip_index == clip:
				animation_structure.update_animation(self, time)

		structure = self.root_struct.first_sub_node
		while structure:
			if structure.base_type == EStructureType.Node:
				structure.update_node_transforms(self)

			structure = structure.next_node

