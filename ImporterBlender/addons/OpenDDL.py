from enum import Enum
from Tree import TreeBase
import Data
import OpenGEX

MaxPrimitiveArraySize = 256


class EStructureType(Enum):
	Root = 0
	Primitive = 1
	Unknown = 2


class EDataResult(Enum):
	MissingSubstructure		= 0, # A structure is missing a substructure of a required type.
	ExtraneousSubstructure	= 1, # A structure contains too many substructures of a legal type.
	InvalidDataFormat		= 2, # The primitive data contained in a structure uses an invalid format (type, subarray size, or state data).
	BrokenRef               = 3	 # The target of a reference does not exist.


class Structure(TreeBase):
	def __init__(self, in_type):
		super().__init__()
		self.type = in_type
		self.base_type = EStructureType.Root
		self.structure_map = dict()
		self.text_location = 0
		self.name = None
		self.is_name_global = True

	def get_key(self):
		return self.name

	def get_first_substructure(self, struct_type):
		local_struct = self.first_sub_node
		while local_struct:
			if local_struct.type == struct_type:
				return local_struct

			local_struct = local_struct.next_node

		return None

	def get_last_substructure(self, struct_type):
		local_struct = self.last_sub_node
		while local_struct:
			if local_struct.type == struct_type:
				return local_struct

			local_struct = local_struct.prev_node

		return None

	def find_structure(self, struct_ref, index = 0):
		if index != 0 or not struct_ref.is_ref_global:
			count = len(struct_ref.name_array)
			if count != 0:
				local_struct = self.structure_map.get(struct_ref.name_array[index])
				if local_struct:
					index += 1
					if index < count:
						local_struct = local_struct.find_structure(struct_ref, index)

				return local_struct

		return None

	def validate_property(self, data_description, identifier):
		return False, None

	def validate_substructure(self, data_description, struct_instance):
		return False

	def set_property(self, data_description, identifier, data_value):
		return False

	# Do we need this?
	def get_state_value(self, identifier, state_value):
		return False

	def process_data(self, data_description):
		local_struct = self.first_sub_node
		while local_struct:
			result = local_struct.process_data(data_description)
			if result != Data.EDataResult.Okay:
				if not data_description.error_structure:
					data_description.error_structure = local_struct

				return result

			local_struct = local_struct.next_node

		return Data.EDataResult.Okay

	def set_base_structure_type(self, base_type):
		self.base_type = base_type


class RootStructure(Structure):
	def __init__(self):
		super().__init__(EStructureType.Root)

	def validate_substructure(self, data_description, struct_instance):
		return data_description.validate_toplevel_structure(struct_instance)


class PrimitiveStructure(Structure):
	def __init__(self, in_type, size = 0, state = False):
		super().__init__(in_type)
		self.base_type = EStructureType.Primitive
		self.array_size = size
		self.state_flag = state


class DataStructure(PrimitiveStructure):
	def __init__(self, in_type):
		super().__init__(in_type)
		self.data_array = []
		self.state_array = []

	def parse_data(self, text_buffer, text_index):
		count = 0
		array_size = self.array_size
		if array_size == 0:
			while True:
				self.data_array.append(None)
				result, text_index, data_value = Data.parse_value(self.type, text_buffer, text_index)
				if result != Data.EDataResult.Okay:
					return result, text_index

				self.data_array[count] = data_value
				text_index = Data.read_whitespaces(text_buffer, text_index)

				if text_buffer[text_index] == ',':
					text_index += 1
					text_index = Data.read_whitespaces(text_buffer, text_index)

					count += 1
					continue
				break
		else:
			super_structure = self.super_node
			state_flag = self.state_flag
			state_value = 0
			while True:
				if state_flag:
					result, text_index, identifier = Data.read_identifier(text_buffer, text_index)
					if result == Data.EDataResult.Okay:
						got_value = super_structure.get_state_value(identifier, state_value)
						if not got_value:
							return Data.EDataResult.PrimitiveInvalidState, text_index

						text_index = Data.read_whitespaces(text_buffer, text_index)

				if text_buffer[text_index] != '{':
					return Data.EDataResult.PrimitiveInvalidFormat, text_index

				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

				if state_flag:
					self.state_array.append(state_value)

				index = 0
				while index < array_size:
					if index != 0:
						if text_buffer[text_index] != ',':
							return Data.EDataResult.PrimitiveArrayUnderSize, text_index

						text_index += 1
						text_index = Data.read_whitespaces(text_buffer, text_index)

					result, text_index, data_value = Data.parse_value(self.type, text_buffer, text_index)
					if result != Data.EDataResult.Okay:
						return result, text_index

					# self.data_array[count * array_size + index] = data_value
					self.data_array.append(data_value)
					text_index = Data.read_whitespaces(text_buffer, text_index)

					index += 1

				c = text_buffer[text_index]
				if c != '}':
					if c == ',':
						return Data.EDataResult.PrimitiveArrayOverSize, text_index
					else:
						return Data.EDataResult.PrimitiveInvalidFormat, text_index

				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

				if text_buffer[text_index] == ',':
					text_index += 1
					text_index = Data.read_whitespaces(text_buffer, text_index)

					count += 1
					continue
				break

		return Data.EDataResult.Okay, text_index


class DataDescription:
	def __init__(self):
		self.structure_map = dict()
		self.root_structure = RootStructure()
		self.error_structure = None
		self.error_line = 0

	def find_structure(self, struct_ref):
		if struct_ref.is_ref_global:
			count = len(struct_ref.name_array)
			if count != 0:
				local_struct = self.structure_map.get(struct_ref.name_array[0])
				if local_struct and count > 1:
					local_struct = local_struct.find_structure(struct_ref, 1)

				return local_struct

		return None

	@staticmethod
	def create_primitive(self, identifier):
		result, text_index, data_value = Data.read_data_type(identifier, 0)
		if result == Data.EDataResult.Okay:
			return DataStructure(data_value)

		return None

	def validate_toplevel_structure(self, struct_instance):
		return True

	def create_structure(self, identifier):
		return None

	def process_data(self):
		return self.root_structure.process_data(self)

	def parse_properties(self, text_buffer, text_index, struct_instance):
		while True:
			result, text_index, identifier = Data.read_identifier(text_buffer, text_index)
			if result != Data.EDataResult.Okay:
				return result, text_index

			text_index = Data.read_whitespaces(text_buffer, text_index)
			property_value = None
			is_property_valid, property_type = struct_instance.validate_property(self, identifier)
			if is_property_valid:
				if property_type != Data.EDataType.Bool:
					if text_buffer[text_index] != '=':
						return Data.EDataResult.PropertySyntaxError, text_index

					text_index += 1
					text_index = Data.read_whitespaces(text_buffer, text_index)

					if property_type == Data.EDataType.Int8:
						result, text_index, property_value = Data.parse_value_int8(text_buffer, text_index)
					elif property_type == Data.EDataType.Int16:
						result, text_index, property_value = Data.parse_value_int16(text_buffer, text_index)
					elif property_type == Data.EDataType.Int32:
						result, text_index, property_value = Data.parse_value_int32(text_buffer, text_index,)
					elif property_type == Data.EDataType.Int64:
						result, text_index, property_value = Data.parse_value_int64(text_buffer, text_index)
					elif property_type == Data.EDataType.UInt8:
						result, text_index, property_value = Data.parse_value_uint16(text_buffer, text_index)
					elif property_type == Data.EDataType.UInt16:
						result, text_index, property_value = Data.parse_value_uint16(text_buffer, text_index)
					elif property_type == Data.EDataType.UInt32:
						result, text_index, property_value = Data.parse_value_uint32(text_buffer, text_index)
					elif property_type == Data.EDataType.UInt64:
						result, text_index, property_value = Data.parse_value_uint64(text_buffer, text_index)
					elif property_type == Data.EDataType.Half:
						result, text_index, property_value = Data.parse_value_half(text_buffer, text_index)
					elif property_type == Data.EDataType.Float:
						result, text_index, property_value = Data.parse_value_float(text_buffer, text_index)
					elif property_type == Data.EDataType.Double:
						result, text_index, property_value = Data.parse_value_double(text_buffer, text_index)
					elif property_type == Data.EDataType.String:
						result, text_index, property_value = Data.parse_value_string(text_buffer, text_index)
					elif property_type == Data.EDataType.Ref:
						result, text_index, property_value = Data.parse_value_refdata(text_buffer, text_index)
					elif property_type == Data.EDataType.Type:
						result, text_index, property_value = Data.parse_value_type(text_buffer, text_index)
					elif property_type == Data.EDataType.Base64:
						result, text_index, property_value = Data.parse_value_base64(text_buffer, text_index)
					else:
						return Data.EDataResult.PropertyInvalidType, text_index

				else:
					if text_buffer[text_index] == '=':
						text_index += 1
						text_index = Data.read_whitespaces(text_buffer, text_index)

						result, text_index, property_value = Data.parse_value_bool(text_buffer, text_index)
					else:
						property_value = True
			else:
				# Read an arbitrary property value of unknown type and discard it.
				if text_buffer[text_index] == '=':
					text_index += 1
					text_index = Data.read_whitespaces(text_buffer, text_index)

					result, text_index, _ = Data.parse_value_bool(text_buffer, text_index)
					if result != Data.EDataResult.Okay:
						result, text_index, _ = Data.parse_value_string(text_buffer, text_index)
						if result != Data.EDataResult.Okay:
							result, text_index, _ = Data.parse_value_refdata(text_buffer, text_index)
							if result != Data.EDataResult.Okay:
								result, text_index, _ = Data.parse_value_type(text_buffer, text_index)
								if result != Data.EDataResult.Okay:
									result, text_index, _ = Data.parse_value_uint64(text_buffer, text_index)
									if result != Data.EDataResult.Okay:
										result, text_index, _ = Data.parse_value_double(text_buffer, text_index)
										if result != Data.EDataResult.Okay:
											result, text_index, _ = Data.parse_value_base64(text_buffer, text_index)
											if result != Data.EDataResult.Okay:
												result = Data.EDataResult.PropertySyntaxError

			if result != Data.EDataResult.Okay:
				return result, text_index
			
			was_set = struct_instance.set_property(self, identifier, property_value)
			if not was_set:
				return Data.EDataResult.PropertySyntaxError, text_index

			if text_buffer[text_index] == ',':
				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)
				continue

			break

		return Data.EDataResult.Okay, text_index

	def parse_structures(self, text_buffer, text_index, root_struct):
		while True:
			result, text_index, identifier = Data.read_identifier(text_buffer, text_index)
			if result != Data.EDataResult.Okay:
				return result, text_index

			primitive_flag = False
			unknown_flag = False

			struct_instance = self.create_primitive(self, identifier)
			if struct_instance:
				primitive_flag = True
			else:
				struct_instance = self.create_structure(identifier)
				if not struct_instance:
					struct_instance = Structure(EStructureType.Unknown)
					unknown_flag = True

			identifier = ""
			struct_instance.text_location = text_index
			root_struct.append_sub_node(struct_instance)

			# text_index should already account identifier len?
			text_index = Data.read_whitespaces(text_buffer, text_index)

			if primitive_flag and text_buffer[text_index] == '[':
				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

				is_negative, text_index = Data.parse_sign(text_buffer, text_index)
				if is_negative:
					return Data.EDataResult.PrimitiveIllegalArraySize, text_index

				result, text_index, value = Data.read_integer_literal(text_buffer, text_index)
				if result != Data.EDataResult.Okay:
					return result, text_index

				if value == 0 or value > MaxPrimitiveArraySize:
					return Data.EDataResult.PrimitiveIllegalArraySize, text_index

				# length of literal already accounted for?
				text_index = Data.read_whitespaces(text_buffer, text_index)

				if text_buffer[text_index] != ']':
					return Data.EDataResult.PrimitiveSyntaxError, text_index

				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

				struct_instance.array_size = value

				if text_buffer[text_index] == '*':
					text_index += 1
					text_index = Data.read_whitespaces(text_buffer, text_index)

					struct_instance.state_flag = True

			
			if (not unknown_flag) and (not root_struct.validate_substructure(self, struct_instance)):
				return Data.EDataResult.InvalidStructure, text_index

			c = text_buffer[text_index]
			x = ord(c) - ord('$')
			x = x & 0xffffffff
			if x < 2:
				text_index += 1

				result, text_index, identifier = Data.read_identifier(text_buffer, text_index)
				if result != Data.EDataResult.Okay:
					return result, text_index

				struct_instance.name = identifier

				is_global = c == '$'
				struct_instance.is_name_global = is_global

				key = struct_instance.get_key()
				if is_global:
					if key in self.structure_map.keys():
						return Data.EDataResult.StructNameExists, text_index

					self.structure_map[key] = struct_instance
				else:
					if key in root_struct.structure_map.keys():
						return Data.EDataResult.StructNameExists, text_index

					root_struct.structure_map[key] = struct_instance

				text_index = Data.read_whitespaces(text_buffer, text_index)

			if (not primitive_flag) and text_buffer[text_index] == '(':
				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

				if text_buffer[text_index] != ')':
					result, text_index = self.parse_properties(text_buffer, text_index, struct_instance)
					if result != Data.EDataResult.Okay:
						return result, text_index

					if text_buffer[text_index] != ')':
						return Data.EDataResult.PropertySyntaxError, text_index

				text_index += 1
				text_index = Data.read_whitespaces(text_buffer, text_index)

			if text_buffer[text_index] != '{':
				return Data.EDataResult.SyntaxError, text_index

			text_index += 1
			text_index = Data.read_whitespaces(text_buffer, text_index)

			if text_buffer[text_index] != '}':
				if primitive_flag:
					result, text_index = struct_instance.parse_data(text_buffer, text_index)
					if result != Data.EDataResult.Okay:
						return result, text_index
				else:
					result, text_index = self.parse_structures(text_buffer, text_index, struct_instance)
					if result != Data.EDataResult.Okay:
						return result, text_index

				if text_buffer[text_index] != '}':
					return Data.EDataResult.SyntaxError, text_index

			text_index += 1
			if len(text_buffer) - 1 == text_index:
				# End of file?
				return Data.EDataResult.Okay, text_index
			text_index = Data.read_whitespaces(text_buffer, text_index)

			if not unknown_flag:
				# Nothing to do?
				x = 0

			c = text_buffer[text_index]
			if ord(c) == 0 or c == '}':
				# Reached either end of file or end of substructures for an enclosing structure.
				break

		return Data.EDataResult.Okay, text_index

	def process_text(self, text_buffer, text_index):
		self.root_structure.purge_sub_tree()

		self.error_structure = None
		self.error_line = 0

		start = text_buffer[text_index]
		buffer_length = len(text_buffer)
		text_index += Data.read_whitespaces(text_buffer, text_index)

		result = Data.EDataResult.Okay
		if ord(text_buffer[text_index]) != 0:
			result, text_index = self.parse_structures(text_buffer, text_index, self.root_structure)
			if result == Data.EDataResult.Okay and (buffer_length - 1) != text_index:
				result = Data.EDataResult.SyntaxError

		if result == Data.EDataResult.Okay:
			result = self.process_data()
			if result != Data.EDataResult.Okay and self.error_structure:
				text_index = self.error_structure.text_location

		if result != Data.EDataResult.Okay:
			line = 1
			while text_buffer[text_index] != start:
				text_index -= 1
				if text_buffer[text_index] == '\n':
					line += 1

			self.error_line = line
			self.root_structure.purge_sub_tree()

		return result
