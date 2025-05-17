import sys
from enum import Enum
import ctypes
import struct

class EDataResult(Enum):
	Okay						= 0
	SyntaxError					= 'SYNT'	## The syntax is invalid.
	IdentifierEmpty				= 'IDEM'	## No identifier was found where one was expected.
	IdentifierIllegalChar		= 'IDIC'	## An identifier contains an illegal character.
	StringInvalid				= 'STIV'	## A string literal is invalid.
	StringIllegalChar			= 'STIC'	## A string literal contains an illegal character.
	StringIllegalEscape			= 'STIE'	## A string literal contains an illegal escape sequence.
	StringEndOfFile				= 'STEF'	## The end of file was reached inside a string literal.
	CharIllegalChar				= 'CHIC'	## A character literal contains an illegal character.
	CharIllegalEscape			= 'CHIE'	## A character literal contains an illegal escape sequence.
	CharEndOfFile				= 'CHEF'	## The end of file was reached inside a character literal.
	BoolInvalid					= 'BLIV'	## A boolean value is not "true", "false", "0", or "1".
	TypeInvalid					= 'TYIV'	## A data type value does not name a primitive type.
	Base64Invalid				= 'BSIV'	## Base64 data is invalid.
	IntegerOverflow				= 'INOV'	## An integer value lies outside the range of representable values for the number of bits in its underlying type.
	FloatOverflow				= 'FLOV'	## A hexadecimal or binary literal used to represent a floating-point value contains more bits than the underlying type.
	FloatInvalid				= 'FLIV'	## A floating-point literal has an invalid format.
	ReferenceInvalid			= 'RFIV'	## A reference uses an invalid syntax.
	StructNameExists			= 'STNE'	## A structure name is equal to a previously used structure name.
	PropertySyntaxError			= 'PPSE'	## A property list contains a syntax error.
	PropertyInvalidType			= 'PPIT'	## A property has specified an invalid type. This error is generated if the $@Structure::ValidateProperty@$ function does not specify a recognized data type.
	PrimitiveSyntaxError		= 'PMSE'	## A primitive data structure contains a syntax error.
	PrimitiveIllegalArraySize	= 'PMAS'	## A primitive data array size is too large.
	PrimitiveInvalidFormat		= 'PMIF'	## A primitive data structure contains data in an invalid format.
	PrimitiveArrayUnderSize		= 'PMUS'	## A primitive array contains too few elements.
	PrimitiveArrayOverSize		= 'PMOS'	## A primitive array contains too many elements.
	PrimitiveInvalidState		= 'PMST'	## A state identifier contained in primitive array data is not recognized. This error is generated when the $@Structure::GetStateValue@$ function returns $false$.
	InvalidStructure			= 'IVST'	## A structure contains a substructure of an invalid type, or a structure of an invalid type appears at the top level of the file. This error is generated when either the $@Structure::ValidateSubstructure@$ function or $@DataDescription::ValidateTopLevelStructure@$ function returns $false$.

class EDataType(Enum):
	Bool							= 'BOOL'	## Boolean.
	Int8							= 'INT8'	## 8-bit signed integer.
	Int16							= 'IN16'	## 16-bit signed integer.
	Int32							= 'IN32'	## 32-bit signed integer.
	Int64							= 'IN64'	## 64-bit signed integer.
	UInt8							= 'UIN8'	## 8-bit unsigned integer.
	UInt16							= 'UI16'	## 16-bit unsigned integer.
	UInt32							= 'UI32'	## 32-bit unsigned integer.
	UInt64							= 'UI64'	## 64-bit unsigned integer.
	Half							= 'HALF'	## 16-bit floating-point.
	Float							= 'FLOT'	## 32-bit floating-point.
	Double							= 'DOUB'	## 64-bit floating-point.
	String							= 'STRG'	## String.
	Ref							    = 'RFNC'	## Reference.
	Type							= 'TYPE'	## Type.
	Base64							= 'BS64'	## Base64 data.

MinusPower10 = [
	0.0, 1e-308, 1e-307, 1e-306, 1e-305, 1e-304, 1e-303, 1e-302, 1e-301, 1e-300, 1e-299, 1e-298, 1e-297, 1e-296, 1e-295, 1e-294, 1e-293, 1e-292, 1e-291, 1e-290, 1e-289, 1e-288, 1e-287, 1e-286, 1e-285, 1e-284, 1e-283, 1e-282, 1e-281, 1e-280, 1e-279, 1e-278,
	1e-277, 1e-276, 1e-275, 1e-274, 1e-273, 1e-272, 1e-271, 1e-270, 1e-269, 1e-268, 1e-267, 1e-266, 1e-265, 1e-264, 1e-263, 1e-262, 1e-261, 1e-260, 1e-259, 1e-258, 1e-257, 1e-256, 1e-255, 1e-254, 1e-253, 1e-252, 1e-251, 1e-250, 1e-249, 1e-248, 1e-247, 1e-246,
	1e-245, 1e-244, 1e-243, 1e-242, 1e-241, 1e-240, 1e-239, 1e-238, 1e-237, 1e-236, 1e-235, 1e-234, 1e-233, 1e-232, 1e-231, 1e-230, 1e-229, 1e-228, 1e-227, 1e-226, 1e-225, 1e-224, 1e-223, 1e-222, 1e-221, 1e-220, 1e-219, 1e-218, 1e-217, 1e-216, 1e-215, 1e-214,
	1e-213, 1e-212, 1e-211, 1e-210, 1e-209, 1e-208, 1e-207, 1e-206, 1e-205, 1e-204, 1e-203, 1e-202, 1e-201, 1e-200, 1e-199, 1e-198, 1e-197, 1e-196, 1e-195, 1e-194, 1e-193, 1e-192, 1e-191, 1e-190, 1e-189, 1e-188, 1e-187, 1e-186, 1e-185, 1e-184, 1e-183, 1e-182,
	1e-181, 1e-180, 1e-179, 1e-178, 1e-177, 1e-176, 1e-175, 1e-174, 1e-173, 1e-172, 1e-171, 1e-170, 1e-169, 1e-168, 1e-167, 1e-166, 1e-165, 1e-164, 1e-163, 1e-162, 1e-161, 1e-160, 1e-159, 1e-158, 1e-157, 1e-156, 1e-155, 1e-154, 1e-153, 1e-152, 1e-151, 1e-150,
	1e-149, 1e-148, 1e-147, 1e-146, 1e-145, 1e-144, 1e-143, 1e-142, 1e-141, 1e-140, 1e-139, 1e-138, 1e-137, 1e-136, 1e-135, 1e-134, 1e-133, 1e-132, 1e-131, 1e-130, 1e-129, 1e-128, 1e-127, 1e-126, 1e-125, 1e-124, 1e-123, 1e-122, 1e-121, 1e-120, 1e-119, 1e-118,
	1e-117, 1e-116, 1e-115, 1e-114, 1e-113, 1e-112, 1e-111, 1e-110, 1e-109, 1e-108, 1e-107, 1e-106, 1e-105, 1e-104, 1e-103, 1e-102, 1e-101, 1e-100,  1e-99,  1e-98,  1e-97,  1e-96,  1e-95,  1e-94,  1e-93,  1e-92,  1e-91,  1e-90,  1e-89,  1e-88,  1e-87,  1e-86,
	1e-85,  1e-84,  1e-83,  1e-82,  1e-81,  1e-80,  1e-79,  1e-78,  1e-77,  1e-76,  1e-75,  1e-74,  1e-73,  1e-72,  1e-71,  1e-70,  1e-69,  1e-68,  1e-67,  1e-66,  1e-65,  1e-64,  1e-63,  1e-62,  1e-61,  1e-60,  1e-59,  1e-58,  1e-57,  1e-56,  1e-55,  1e-54,
	1e-53,  1e-52,  1e-51,  1e-50,  1e-49,  1e-48,  1e-47,  1e-46,  1e-45,  1e-44,  1e-43,  1e-42,  1e-41,  1e-40,  1e-39,  1e-38,  1e-37,  1e-36,  1e-35,  1e-34,  1e-33,  1e-32,  1e-31,  1e-30,  1e-29,  1e-28,  1e-27,  1e-26,  1e-25,  1e-24,  1e-23,  1e-22,
	1e-21,  1e-20,  1e-19,  1e-18,  1e-17,  1e-16,  1e-15,  1e-14,  1e-13,  1e-12,  1e-11,  1e-10,   1e-9,   1e-8,   1e-7,   1e-6,   1e-5,   1e-4,   1e-3,   1e-2,   1e-1,    1.0
]

PlusPower10 = [
	1.0,   1e1,   1e2,   1e3,   1e4,   1e5,   1e6,   1e7,   1e8,   1e9,  1e10,  1e11,  1e12,  1e13,  1e14,  1e15,  1e16,  1e17,  1e18,  1e19,  1e20,  1e21,  1e22,  1e23,  1e24,  1e25,  1e26,  1e27,  1e28,  1e29,  1e30,  1e31,
	1e32,  1e33,  1e34,  1e35,  1e36,  1e37,  1e38,  1e39,  1e40,  1e41,  1e42,  1e43,  1e44,  1e45,  1e46,  1e47,  1e48,  1e49,  1e50,  1e51,  1e52,  1e53,  1e54,  1e55,  1e56,  1e57,  1e58,  1e59,  1e60,  1e61,  1e62,  1e63,
	1e64,  1e65,  1e66,  1e67,  1e68,  1e69,  1e70,  1e71,  1e72,  1e73,  1e74,  1e75,  1e76,  1e77,  1e78,  1e79,  1e80,  1e81,  1e82,  1e83,  1e84,  1e85,  1e86,  1e87,  1e88,  1e89,  1e90,  1e91,  1e92,  1e93,  1e94,  1e95,
	1e96,  1e97,  1e98,  1e99, 1e100, 1e101, 1e102, 1e103, 1e104, 1e105, 1e106, 1e107, 1e108, 1e109, 1e110, 1e111, 1e112, 1e113, 1e114, 1e115, 1e116, 1e117, 1e118, 1e119, 1e120, 1e121, 1e122, 1e123, 1e124, 1e125, 1e126, 1e127,
	1e128, 1e129, 1e130, 1e131, 1e132, 1e133, 1e134, 1e135, 1e136, 1e137, 1e138, 1e139, 1e140, 1e141, 1e142, 1e143, 1e144, 1e145, 1e146, 1e147, 1e148, 1e149, 1e150, 1e151, 1e152, 1e153, 1e154, 1e155, 1e156, 1e157, 1e158, 1e159,
	1e160, 1e161, 1e162, 1e163, 1e164, 1e165, 1e166, 1e167, 1e168, 1e169, 1e170, 1e171, 1e172, 1e173, 1e174, 1e175, 1e176, 1e177, 1e178, 1e179, 1e180, 1e181, 1e182, 1e183, 1e184, 1e185, 1e186, 1e187, 1e188, 1e189, 1e190, 1e191,
	1e192, 1e193, 1e194, 1e195, 1e196, 1e197, 1e198, 1e199, 1e200, 1e201, 1e202, 1e203, 1e204, 1e205, 1e206, 1e207, 1e208, 1e209, 1e210, 1e211, 1e212, 1e213, 1e214, 1e215, 1e216, 1e217, 1e218, 1e219, 1e220, 1e221, 1e222, 1e223,
	1e224, 1e225, 1e226, 1e227, 1e228, 1e229, 1e230, 1e231, 1e232, 1e233, 1e234, 1e235, 1e236, 1e237, 1e238, 1e239, 1e240, 1e241, 1e242, 1e243, 1e244, 1e245, 1e246, 1e247, 1e248, 1e249, 1e250, 1e251, 1e252, 1e253, 1e254, 1e255,
	1e256, 1e257, 1e258, 1e259, 1e260, 1e261, 1e262, 1e263, 1e264, 1e265, 1e266, 1e267, 1e268, 1e269, 1e270, 1e271, 1e272, 1e273, 1e274, 1e275, 1e276, 1e277, 1e278, 1e279, 1e280, 1e281, 1e282, 1e283, 1e284, 1e285, 1e286, 1e287,
	1e288, 1e289, 1e290, 1e291, 1e292, 1e293, 1e294, 1e295, 1e296, 1e297, 1e298, 1e299, 1e300, 1e301, 1e302, 1e303, 1e304, 1e305, 1e306, 1e307, 1e308, sys.float_info.max
]

HexadecimalCharValue = [
	0,  1,  2,  3,  4,  5,  6,  7,  8,  9, -1, -1, -1, -1, -1, -1,
	-1, 10, 11, 12, 13, 14, 15, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	-1, 10, 11, 12, 13, 14, 15
]

IdentifierCharState = [
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
	0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1,
	0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 2,
	2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
	2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
	2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
	2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2
]

Base64CharValue = [
	-1, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
	-2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
	-1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
	-1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
]


class StructureRef:
	def __init__(self):
		self.name_array = []
		self.is_ref_global = True

	def reset(self, is_global = True):
		del self.name_array[:]
		self.is_ref_global = is_global


class Buffer:
	def __init__(self):
		self.char_array = []

	def allocate_buffer(self, size):
		self.char_array = [None] * size


def max_zero(x):
	return x & ~(x >> 31)


def read_whitespaces(text_buffer, text_index):
	while True:
		c = text_buffer[text_index]
		if ord(c) == 0:
			break

		if ord(c) >= 33: # '!' onwards
			if c != '/':
				break
			
			c = text_buffer[text_index + 1]
			if c == '/':
				text_index += 2
				while True:
					c = text_buffer[text_index]
					if ord(c) == 0:
						return text_index

					text_index += 1

					if ord(c) == 10:
						break

				continue
			
			elif c == '*':
				text_index += 2
				while True:
					c = text_buffer[text_index]
					if ord(c) == 0:
						return text_index

					text_index += 1
					if c == '*' and text_buffer[text_index] == '/':
						text_index += 1
						break

				continue
			break
		text_index += 1

	return text_index


def read_identifier(text_buffer, text_index):
	initial_index = text_index
	character = text_buffer[initial_index]
	ascii_value = ord(character)
	state = IdentifierCharState[ascii_value]

	identifier = ""

	if state == 1:
		if ascii_value < ord('A'):
			return EDataResult.IdentifierIllegalChar, text_index, identifier

		text_index += 1
		while 1:
			character = text_buffer[text_index]
			ascii_value = ord(character)
			state = IdentifierCharState[ascii_value]
			if state == 1:
				text_index += 1
				continue
			elif state == 2:
				return EDataResult.IdentifierIllegalChar, text_index, identifier
			
			break

		identifier = text_buffer[initial_index:text_index]
		return EDataResult.Okay, text_index, identifier
	elif state == 2:
		return EDataResult.IdentifierIllegalChar, text_index, identifier

	return EDataResult.IdentifierEmpty, text_index, identifier


def parse_sign(text_buffer, text_index):
	c = text_buffer[text_index]
	if c == '-':
		text_index += 1
		text_index = read_whitespaces(text_buffer, text_index)
		return True, text_index
	
	if c == '+':
		text_index += 1
		text_index = read_whitespaces(text_buffer, text_index)

	return False, text_index


def read_hexadecimal_literal(text_buffer, text_index):
	byte = text_buffer[text_index + 2]
	text_index += 2
	value = 0
	digit_flag = False
	
	while True:
		c = ord(text_buffer[text_index]) - ord('0')
		c = c & 0xffffffff
		if c >= 55:
			break

		x = HexadecimalCharValue[c]
		if x >= 0:
			if (value >> 60) != 0:
				return EDataResult.IntegerOverflow, text_index, None

			value = (value << 4) | x
			digit_flag = True
		else:
			if (c != 47) or not digit_flag:
				break
			digit_flag = False
		
		text_index += 1

	if not digit_flag:
		return EDataResult.SyntaxError, text_index, None

	return EDataResult.Okay, text_index, value


def read_octal_literal(text_buffer, text_index):
	# TODO
	return EDataResult, text_index, None


def read_binary_literal(text_buffer, text_index):
	# TODO
	return EDataResult, text_index, None


def read_escape_char(text_buffer, text_index):
	c = text_buffer[text_index]

	if c == '\"' or c == '\'' or c == '?' or c == '\\':
		return 1, c
	elif c == 'a':
		return 1, '\a'
	elif c == 'b':
		return 1, '\b'
	elif c == 'f':
		return 1, '\f'
	elif c == 'n':
		return 1, '\n'
	elif c == 'r':
		return 1, '\r'
	elif c == 't':
		return 1, '\t'
	elif c == 'v':
		return 1, '\v'
	elif c == 'x':
		c = ord(text_buffer[text_index + 1]) - ord('0')
		if c < 55:
			x = HexadecimalCharValue[c]
			if x >= 0:
				c = ord(text_buffer[text_index + 2]) - ord('0')
				if c < 55:
					y = HexadecimalCharValue[c]
					if y >= 0:
						value = str((x << 4) | y)
						return 3, value
	return 0, None


def read_char_literal(text_buffer, text_index):
	value = 0
	while True:
		c = text_buffer[text_index]
		if ord(c) == 0 or c == '\'':
			break

		if ord(c) < 32 or c >= 127:
			return EDataResult.CharIllegalChar, text_index, None

		if c != '\\':
			if (value >> 56) != 0:
				return EDataResult.IntegerOverflow, text_index, None
			
			value = (value << 8) | c
			text_index += 1
		else:
			length, x = read_escape_char(text_buffer, text_index + 1)
			if length == 0:
				return EDataResult.CharIllegalEscape, text_index, None

			if (value >> 56) != 0:
				return EDataResult.IntegerOverflow, text_index, None

			value = (value << 8) | ord(x)
			text_index += length

	return EDataResult.Okay, text_index, value


def read_decimal_literal(text_buffer, text_index):
	value = 0
	digit_flag = False
	
	while True:
		c = text_buffer[text_index]
		x = ord(c) - ord('0')
		x = x & 0xffffffff
		if x < 10:
			if value >= 0x199999999999999A:
				return EDataResult.IntegerOverflow, text_index, None

			w = value
			value = value * 10 + x

			if w >= 9 and value < 9:
				return EDataResult.IntegerOverflow, text_index, None

			digit_flag = True
		else:
			if x != 47 or not digit_flag:
				break
			digit_flag = False
		
		text_index += 1

	if not digit_flag:
		return EDataResult.SyntaxError, text_index, None

	return EDataResult.Okay, text_index, value


def read_integer_literal(text_buffer, text_index):
	c = text_buffer[text_index]
	if c == '0':
		c = text_buffer[text_index + 1]

		if c == 'x' or c == 'X':
			return read_hexadecimal_literal(text_buffer, text_index)

		if c == 'o' or c == 'O':
			return read_octal_literal(text_buffer, text_index)

		if c == 'b' or c == 'B':
			return read_binary_literal(text_buffer, text_index)
		
	elif c == '\'':
		text_index += 1
		result, text_index, value = read_char_literal(text_buffer, text_index)
		if result == EDataResult.Okay:
			if text_buffer[text_index + 1] != '\'':
				return EDataResult.CharEndOfFile, text_index, None

			text_index += 2 # Not sure?
		return result, text_index, value

	return read_decimal_literal(text_buffer, text_index)


def read_bool_literal(text_buffer, text_index):
	c = text_buffer[text_index]
	x = ord(c) - ord('0')
	x = x & 0xffffffff
	if x < 2:
		value = c != '0'
		text_index += 1
		return EDataResult.Okay, text_index, value
	elif c == 'f':
		c1 = text_buffer[text_index + 1]
		c2 = text_buffer[text_index + 2]
		c3 = text_buffer[text_index + 3]
		c4 = text_buffer[text_index + 4]
		if (c1 == 'a') and (c2 == 'l') and (c3 == 's') and (c4 == 'e'):
			value = False
			text_index += 5
			return EDataResult.Okay, text_index, value
	elif c == 't':
		c1 = text_buffer[text_index + 1]
		c2 = text_buffer[text_index + 2]
		c3 = text_buffer[text_index + 3]
		if (c1 == 'r') and (c2 == 'u') and (c3 == 'e'):
			value = True
			text_index += 4
			return EDataResult.Okay, text_index, value

	return EDataResult.BoolInvalid, text_index, None


def read_float_literal(text_buffer, text_index):
	c = text_buffer[text_index]
	value = None
	if c == '0':
		c = text_buffer[text_index + 1]
		if (c == 'x') or (c == 'X'):
			result, text_index, v = read_hexadecimal_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_float)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow, text_index, None

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

		if (c == 'o') or (c == 'O'):
			result, text_index, v = read_octal_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_float)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow, text_index, None

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

		if (c == 'b') or (c == 'B'):
			result, text_index, v = read_binary_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_float)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow, text_index, None

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

	v = 0.0
	digit_flag = False
	whole_flag = False
	while True:
		x = ord(text_buffer[text_index]) - ord('0')
		x = x & 0xffffffff
		if x < 10:
			v = v * 10 + float(x)
			digit_flag = True
			whole_flag = True
		elif x == 47:
			if not digit_flag:
				return EDataResult.FloatInvalid, text_index, None

			digit_flag = False
		else:
			break

		text_index += 1

	if whole_flag & (not digit_flag):
		return EDataResult.FloatInvalid, text_index, None

	fraction_flag = False
	c = text_buffer[text_index]
	if c == '.':
		digit_flag = False
		decimal = float(10.0)
		text_index += 1  # Not sure?

		while True:
			x = ord(text_buffer[text_index]) - ord('0')
			x = x & 0xffffffff
			if x < 10:
				v += float(x) / decimal
				digit_flag = True
				whole_flag = True
				decimal *= 10
			elif x == 47:
				if not digit_flag:
					return EDataResult.FloatInvalid, text_index, None

				digit_flag = False
			else:
				break
			text_index += 1

		if fraction_flag & (not digit_flag):
			return EDataResult.FloatInvalid, text_index, None

		c = text_buffer[text_index]

	if not (whole_flag | fraction_flag):
		return EDataResult.FloatInvalid, text_index, None

	if (c == 'e') or (c == 'E'):
		is_negative = False
		text_index += 1
		c = text_buffer[text_index]

		if c == '-':
			is_negative = True
			text_index += 1
		elif c == '+':
			text_index += 1

		exponent = 0
		digit_flag = False
		while True:
			x = ord(text_buffer[text_index]) - ord('0')
			x = x & 0xffffffff
			if x < 10:
				exponent = min(exponent * 10 + x, 65535)
				digit_flag = True
			elif x == 47:
				if not digit_flag:
					return EDataResult.FloatInvalid, text_index, None

				digit_flag = False
			else:
				break

			text_index += 1

		if not digit_flag:
			return EDataResult.FloatInvalid, text_index, None

		if is_negative:
			v *= MinusPower10[max_zero(309 - exponent)]
		else:
			v *= PlusPower10[min(exponent, 309)]

	data_value = float(v)
	return EDataResult.Okay, text_index, data_value


def read_double_literal(text_buffer, text_index):
	c = text_buffer[text_index]
	value = 0.0
	if c == '0':
		c = text_buffer[text_index + 1]
		if (c == 'x') or (c == 'X'):
			result, text_index, v = read_hexadecimal_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_double)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

		if (c == 'o') or (c == 'O'):
			result, text_index, v = read_octal_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_double)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

		if (c == 'b') or (c == 'B'):
			result, text_index, v = read_binary_literal(text_buffer, text_index)
			if result == EDataResult.Okay:
				type_sizeof = ctypes.sizeof(ctypes.c_double)
				if v > ((1 << (type_sizeof * 8 - 1)) - 1) * 2 + 1:
					return EDataResult.FloatOverflow

				value = struct.unpack('f', struct.pack('I', v))[0]

			return EDataResult.Okay, text_index, value

	v = 0.0
	digit_flag = False
	whole_flag = False
	while True:
		x = ord(text_buffer[text_index]) - ord('0')
		x = x & 0xffffffff
		if x < 10:
			v = v * 10 + float(x)
			digit_flag = True
			whole_flag = True
		elif x == 47:
			if not digit_flag:
				return EDataResult.FloatInvalid, text_index, None

			digit_flag = False
		else:
			break

		text_index += 1

	if whole_flag & (not digit_flag):
		return EDataResult.FloatInvalid

	fraction_flag = False
	c = text_buffer[text_index]
	if c == '.':
		digit_flag = False
		decimal = float(10.0)
		text_index += 1  # Not sure?

		while True:
			x = ord(text_buffer[text_index]) - ord('0')
			x = x & 0xffffffff
			if x < 10:
				v += float(x) / decimal
				digit_flag = True
				whole_flag = True
				decimal *= 10
			elif x == 47:
				if not digit_flag:
					return EDataResult.FloatInvalid, text_index, None

				digit_flag = False
			else:
				break
			text_index += 1

		if fraction_flag & (not digit_flag):
			return EDataResult.FloatInvalid, text_index, None

		c = text_buffer[text_index]

	if not (whole_flag | fraction_flag):
		return EDataResult.FloatInvalid, text_index, None

	if (c == 'e') or (c == 'E'):
		is_negative = False
		text_index += 1
		c = text_buffer[text_index]

		if c == '-':
			is_negative = True
			text_index += 1
		elif c == '+':
			text_index += 1

		exponent = 0
		digit_flag = False
		while True:
			x = ord(text_buffer[text_index]) - ord('0')
			x = x & 0xffffffff
			if x < 10:
				exponent = min(exponent * 10 + x, 65535)
				digit_flag = True
			elif x == 47:
				if not digit_flag:
					return EDataResult.FloatInvalid, text_index, None

				digit_flag = False
			else:
				break

			text_index += 1

		if not digit_flag:
			return EDataResult.FloatInvalid, text_index, None

		if is_negative:
			v *= MinusPower10[max_zero(309 - exponent)]
		else:
			v *= PlusPower10[min(exponent, 309)]

	value = float(v)
	return EDataResult.Okay, text_index, value


def validate_unicode_char(text_buffer, text_index):
	c = ord(text_buffer[text_index])
	if c >= 0:
		return 1

	byte1 = c & 0xFF
	if byte1 - 0xC2 < 0x33:
		byte2 = ord(text_buffer[text_index + 1])
		if (byte2 & 0xC0) == 0x80:
			if byte1 < 0xE0:
				return 2

			byte3 = ord(text_buffer[text_index + 2])
			if (byte3 & 0xC0) == 0x80:
				if byte1 < 0xF0:
					x = ((byte1 << 12) & 0x00F000) | ((byte2 << 6) & 0x000FC0) | (byte3 & 0x00003F)
					if x - 0x0800 < 0xF800:
						return 3
					return 0

				byte4 = ord(text_buffer[text_index + 3])
				if (byte4 & 0xC0) == 0x80:
					x = ((byte1 << 18) & 0x1C0000) | ((byte2 << 12) & 0x03F000) | ((byte3 << 6) & 0x000FC0) | (byte4 & 0x00003F)
					if x - 0x00010000 < 0x00100000:
						return 4

	return 0


def write_unicode_char(text, code):
	if code <= 0x00007F:
		text[0] = chr(code)
		return 1

	if code <= 0x0007FF:
		text[0] = chr(((code >> 6) & 0x1F) | 0xC0)
		text[1] = chr((code & 0x3F) | 0x80)
		return 2

	if code <= 0x00FFFF:
		text[0] = chr(((code >> 12) & 0x0F) | 0xE0)
		text[1] = chr(((code >> 6) & 0x3F) | 0x80)
		text[2] = chr((code & 0x3F) | 0x80)
		return 3

	if code <= 0x10FFFF:
		text[0] = chr(((code >> 18) & 0x07) | 0xF0)
		text[1] = chr(((code >> 12) & 0x3F) | 0x80)
		text[2] = chr(((code >> 6) & 0x3F) | 0x80)
		text[3] = chr((code & 0x3F) | 0x80)
		return 4

	return 0


def compare_text(s1, s1_index, s2, s2_index, max_len):
	a = 0
	while True:
		max_len -= 1
		if max_len < 0:
			break

		x = s1[s1_index + 1]
		y = s2[s2_index + 1]

		if x != y:
			return False

		if ord(x) == 0:
			break
		
		a += 1

	return True


def read_string_escape_char(text_buffer, text_index, string_len, string = None):
	c = ord(text_buffer[text_index])
	if c == ord('u'):
		code = 0
		a = text_index + 1
		while a <= (text_index + 4):
			c = ord(text_buffer[a]) - ord('0')
			c = c & 0xffffffff
			if c >= 55:
				return 0, string_len

			x = HexadecimalCharValue[c]
			if x < 0:
				return 0, string_len

			code = (code << 4) | x
			a += 1

		if code != 0:
			if string:
				string_len = write_unicode_char(string, code)
			else:
				string_len = 1 + (code >= 0x000080) + (code >= 0x000800)

			return 5, string_len

	if c == ord('U'):
		code = 0
		a = text_buffer + 1
		while a <= (text_index + 6):
			c = ord(text_buffer[a]) - ord('0')
			c = c & 0xffffffff
			if c >= 55:
				return 0, string_len

			x = HexadecimalCharValue[c]
			if x < 0:
				return 0, string_len

			code = (code << 4) | x
			a += 1

		if code != 0 and code <= 0x10FFFF:
			if string:
				string_len = write_unicode_char(string, code)
			else:
				string_len = 1 + (code >= 0x000080) + (code >= 0x000800) + (code >= 0x010000)

			return 7, string_len
	else:
		text_len, value = read_escape_char(text_buffer, text_index)
		if text_len != 0:
			if string:
				string = chr(value)

			string_len = 1
			return text_len, string_len

	return 0, string_len


def read_string_literal(text_buffer, text_index):
	count = 0
	string = ""
	while True:
		c = text_buffer[text_index]
		if (ord(c) == 0) or (c == '\"'):
			break

		if (ord(c) < 32) or (ord(c) == 127):
			return EDataResult.StringIllegalChar, text_index, string

		if c != '\\':
			length = validate_unicode_char(text_buffer, text_index)
			if length == 0:
				return EDataResult.StringIllegalChar, text_index, string

			a = 0
			while a < length:
				# Appending/Concatenation :(
				string += text_buffer[text_index + a]
				a += 1

			text_index += length
			count += length
		else:
			string_len_local = 0
			text_index += 1
			text_len = read_string_escape_char(text_buffer, text_index, string_len_local, string)
			if text_len == 0:
				return EDataResult.StringIllegalEscape, text_index, string

			text_index += text_len
			count += string_len_local

	return EDataResult.Okay, text_index, string


def read_data_type(text_buffer, text_index):
	# Python strings are not null terminated
	c = text_buffer[text_index]
	length = 0
	if c == 'i':
		if (text_buffer[text_index + 1] == 'n') and (text_buffer[text_index + 2] == 't'):
			length = 3
			byte_pos = text_index + length - 1
			if text_buffer[byte_pos + 1] == '8':
				data_value = EDataType.Int8
				text_index += length + 1
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '1' and text_buffer[byte_pos + 2] == '6':
				data_value = EDataType.Int16
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '3' and text_buffer[byte_pos + 2] == '2':
				data_value = EDataType.Int32
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '6' and text_buffer[byte_pos + 2] == '4':
				data_value = EDataType.Int64
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value
	elif c == 'u':
		if compare_text(text_buffer, text_index + 1, "nsigned_int", 0, 11):
			length = 12
		elif compare_text(text_buffer, text_index + 1, "int", 0, 3):
			length = 4
		else: 
			return EDataResult.TypeInvalid, text_index, None
		byte_pos = text_index + length - 1

		if text_buffer[byte_pos + 1] == '8':
			data_value = EDataType.UInt8
			text_index += length + 1
			return EDataResult.Okay, text_index, data_value

		if text_buffer[byte_pos + 1] == '1' and text_buffer[byte_pos + 2] == '6':
			data_value = EDataType.UInt16
			text_index += length + 2
			return EDataResult.Okay, text_index, data_value

		if text_buffer[byte_pos + 1] == '3' and text_buffer[byte_pos + 2] == '2':
			data_value = EDataType.UInt32
			text_index += length + 2
			return EDataResult.Okay, text_index, data_value

		if text_buffer[byte_pos + 1] == '6' and text_buffer[byte_pos + 2] == '4':
			data_value = EDataType.UInt64
			text_index += length + 2
			return EDataResult.Okay, text_index, data_value
	elif c == 'f':
		if compare_text(text_buffer, text_index + 1, "loat", 0, 4):
			length = 5
			byte_pos = text_index + length - 1
			if len(text_buffer) == length:
				data_value = EDataType.Float
				text_index += length
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '1' and text_buffer[byte_pos + 2] == '6':
				data_value = EDataType.Half
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '3' and text_buffer[byte_pos + 2] == '2':
				data_value = EDataType.Float
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value

			if text_buffer[byte_pos + 1] == '6' and text_buffer[byte_pos + 2] == '4':
				data_value = EDataType.Double
				text_index += length + 2
				return EDataResult.Okay, text_index, data_value

			data_value = EDataType.Float
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 'b':
		if compare_text(text_buffer, text_index + 1, "ool", 0, 3):
			length = 4
			if compare_text(text_buffer, text_index + 1, "ase64", 0, 5):
				data_value = EDataType.Base64
				text_index += 6
				return EDataResult.Okay, text_index, data_value

			data_value = EDataType.Bool
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 'h':
		if compare_text(text_buffer, text_index + 1, "alf", 0, 3):
			length = 4
			data_value = EDataType.Half
			text_buffer += length
			return EDataResult.Okay, text_index, data_value
	elif c == 'd':
		if compare_text(text_buffer, text_index + 1, "ouble", 0, 5):
			length = 6
			data_value = EDataType.Double
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 's':
		if compare_text(text_buffer, text_index + 1, "tring", 0, 5):
			length = 6
			data_value = EDataType.String
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 'r':
		if (text_buffer[text_index + 1] == 'e') and (text_buffer[text_index + 2] == 'f'):
			length = 3
			data_value = EDataType.Ref
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 't':
		if compare_text(text_buffer, text_index + 1, "ype", 0, 3):
			length = 4
			data_value = EDataType.Type
			text_index += length
			return EDataResult.Okay, text_index, data_value
	elif c == 'z':
			data_value = EDataType.Base64
			text_index += 1
			return EDataResult.Okay, text_index, data_value

	return EDataResult.TypeInvalid, text_index, None


def parse_value_bool(text_buffer, text_index):
	# if not data_value:
	# data_value = True

	result, text_index, data_value = read_bool_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	text_index = read_whitespaces(text_buffer, text_index)
	return EDataResult.Okay, text_index, data_value


def parse_value_int8(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	data_value = None
	if not is_negative:
		if unsigned_value > 0x7F:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_byte(unsigned_value), text_index, None
		data_value = int(unsigned_value), text_index, None
	else:
		if unsigned_value > 0x80:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_byte(-1 * unsigned_value)
		data_value = int(-1 * unsigned_value)

	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_int16(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	data_value = None
	if not is_negative:
		if unsigned_value > 0x7FFF:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_short(unsigned_value)
		data_value = int(unsigned_value)
	else:
		if unsigned_value > 0x8000:
			return EDataResult.IntegerOverflow, text_index, None

		#data_value = ctypes.c_short(-1 * unsigned_value)
		data_value = int(-1 * unsigned_value)

	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_int32(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	data_value = None
	if not is_negative:
		if unsigned_value > 0x7FFFFFFF:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_int(unsigned_value)
		data_value = int(unsigned_value)
	else:
		if unsigned_value > 0x80000000:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_int(-1 * unsigned_value)
		data_value = int(-1 * unsigned_value)

	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_int64(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	data_value = None
	if not is_negative:
		if unsigned_value > 0x7FFFFFFFFFFFFFFF:
			return EDataResult.IntegerOverflow, text_index, None

		# data_value = ctypes.c_longlong(unsigned_value)
		data_value = int(unsigned_value)
	else:
		if unsigned_value > 0x8000000000000000:
			return EDataResult.IntegerOverflow, text_index, None

		#data_value = ctypes.c_longlong(-1 * unsigned_value)
		data_value = int(-1 * unsigned_value)

	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_uint8(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		unsigned_value = (-1 * unsigned_value) & 0xff
	
	# data_value = ctypes.c_ubyte(unsigned_value)
	data_value = int(unsigned_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_uint16(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		unsigned_value = (-1 * unsigned_value) & 0xffff
	
	# data_value = ctypes.c_ushort(unsigned_value)
	data_value = int(unsigned_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_uint32(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		unsigned_value = (-1 * unsigned_value) & 0xffffffff
	
	# data_value = ctypes.c_uint(unsigned_value)
	data_value = int(unsigned_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_uint64(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, unsigned_value = read_integer_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		unsigned_value = (-1 * unsigned_value) & 0xffffffffffffffff
	
	# data_value = ctypes.c_ulonglong(unsigned_value)
	data_value = int(unsigned_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_half(text_buffer, text_index):
	# TODO
	return EDataResult.Okay, text_index, None


def parse_value_float(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, float_value = read_float_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		float_value = -1.0 * float_value

	# data_value = ctypes.c_float(float_value)
	data_value = float(float_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_double(text_buffer, text_index):
	is_negative, text_index = parse_sign(text_buffer, text_index)

	result, text_index, double_value = read_double_literal(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result, text_index, None

	if is_negative:
		double_value = -1.0 * double_value

	#data_value = ctypes.c_double(double_value)
	data_value = float(double_value)
	text_index = read_whitespaces(text_buffer, text_index)

	return EDataResult.Okay, text_index, data_value


def parse_value_string(text_buffer, text_index):
	if text_buffer[text_index] != '"':
		return EDataResult.StringInvalid

	while True:
		text_index += 1

		result, text_index, data_value = read_string_literal(text_buffer, text_index)
		if result != EDataResult.Okay:
			return result, text_index, None

		if text_buffer[text_index] != '"':
			return EDataResult.StringInvalid, text_index, None

		text_index += 1
		text_index = read_whitespaces(text_buffer, text_index)

		if text_buffer[text_index] != '"':
			break

	return EDataResult.Okay, text_index, data_value


def parse_value_refdata(text_buffer, text_index):
	c = text_buffer[text_index]
	data_value = StructureRef()
	data_value.reset(c != '%')

	x = ord(c) - ord('$')
	x = x & 0xffffffff
	if x > 2:
		byte_0 = text_buffer[text_index]
		byte_1 = text_buffer[text_index + 1]
		byte_2 = text_buffer[text_index + 2]
		byte_3 = text_buffer[text_index + 3]
		if byte_0 == 'n' and byte_1 == 'u' and byte_2 == 'l' and byte_3 == 'l':
			text_index += 4
			text_index = read_whitespaces(text_buffer, text_index)
			return EDataResult.Okay, text_index, data_value

		return EDataResult.ReferenceInvalid

	while True:
		text_index += 1

		result, text_index, identifier = read_identifier(text_buffer, text_index)
		if result != EDataResult.Okay:
			return result, text_index, data_value

		if data_value:
			data_value.name_array.append(identifier)

		text_index = read_whitespaces(text_buffer, text_index)

		if text_buffer[text_index] != '%':
			break

	return EDataResult.Okay, text_index, data_value


def parse_value_type(text_buffer, text_index):
	discard = True
	#if not data_value:
		#data_value = True #Not sure?

	result, text_index, data_value = read_data_type(text_buffer, text_index)
	if result != EDataResult.Okay:
		return result

	text_index = read_whitespaces(text_buffer, text_index)
	return EDataResult.Okay, text_index, data_value


def parse_value_base64(text_buffer, text_index):
	text_len = 0
	code_len = 0
	data_value = Buffer()
	while True:
		z = Base64CharValue[ord(text_buffer[text_index + text_len])]
		if z >= 0:
			code_len += 1
		elif z == -1:
			break

		text_len += 1

	m = code_len & 3
	if (code_len & 3) == 1:
		return EDataResult.Base64Invalid, text_index, data_value

	if text_buffer[text_index + text_len] == '=':
		if m == 0:
			return EDataResult.Base64Invalid, text_index, data_value

		text_len += 1
		while Base64CharValue[ord(text_buffer[text_index + text_len])] == -2:
			text_len += 1

		if text_buffer[text_index + text_len] == '=':
			if m == 3:
				return EDataResult.Base64Invalid, text_index, data_value

			text_len += 1
			while Base64CharValue[ord(text_buffer[text_index + text_len])] == -2:
				text_len += 1

	text_index += text_len

	byte_len = (code_len * 6) >> 3
	data_value.allocate_buffer(byte_len)

	text_len = 0
	code_len = 0
	bits = 0
	array_index = 0

	while True:
		z = Base64CharValue[ord(text_buffer[text_index + text_len])]
		if z >= 0:
			bits = (bits << 6) | z
			code_len += 1
			if (code_len & 3) == 0:
				data_value.char_array[array_index] = (bits >> 16) & 0xFF
				data_value.char_array[array_index + 1] = (bits >> 8) & 0xFF
				data_value.char_array[array_index + 2] = bits & 0xFF
				array_index += 3
		elif z == -1:
			break

		text_len += 1

	if m >= 2:
		if m == 3:
			data_value.char_array[0] = (bits >> 10) & 0xFF
			data_value.char_array[1] = (bits >> 2) & 0xFF
		else:
			data_value.char_array[0] = (bits >> 4) & 0xFF

	return EDataResult.Okay, text_index, data_value


def parse_value(in_type, text_buffer, text_index):
	if in_type == EDataType.Bool:
		return parse_value_bool(text_buffer, text_index)
	elif in_type == EDataType.Int8:
		return parse_value_int8(text_buffer, text_index)
	elif in_type == EDataType.Int16:
		return parse_value_int16(text_buffer, text_index)
	elif in_type == EDataType.Int32:
		return parse_value_int32(text_buffer, text_index)
	elif in_type == EDataType.Int64:
		return parse_value_int64(text_buffer, text_index)
	elif in_type == EDataType.UInt8:
		return parse_value_uint8(text_buffer, text_index)
	elif in_type == EDataType.UInt16:
		return parse_value_uint16(text_buffer, text_index)
	elif in_type == EDataType.UInt32:
		return parse_value_uint32(text_buffer, text_index)
	elif in_type == EDataType.UInt64:
		return parse_value_uint64(text_buffer, text_index)
	elif in_type == EDataType.Half:
		# @TODO Deal with half float in python
		#return parse_value_half(text_buffer, text_index, data_value)
		return parse_value_float(text_buffer, text_index)
	elif in_type == EDataType.Float:
		return parse_value_float(text_buffer, text_index)
	elif in_type == EDataType.Double:
		return parse_value_double(text_buffer, text_index)
	elif in_type == EDataType.String:
		return parse_value_string(text_buffer, text_index)
	elif in_type == EDataType.Ref:
		return parse_value_refdata(text_buffer, text_index)
	elif in_type == EDataType.Type:
		return parse_value_type(text_buffer, text_index)
	elif in_type == EDataType.Base64:
		return parse_value_base64(text_buffer, text_index)
	else:
		return EDataResult.TypeInvalid, text_index, None
