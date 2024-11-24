# =============================================================
# 
#  Open Game Engine Exchange
#  http://opengex.org/
# 
#  Export plugin for Blender
#  by Eric Lengyel
#    updated for blender 2.80 by Joel Davis
# 	 updated with some fixes by Miguel Cartaxo
#
#  Version 2.9
# 
#  Copyright 2017, Terathon Software LLC
# 
#  This software is licensed under the Creative Commons
#  Attribution-ShareAlike 3.0 Unported License:
# 
#  http://creativecommons.org/licenses/by-sa/3.0/deed.en_US
# 
# =============================================================

bl_info = {
	"name": "OpenGEX (.ogex)",
	"description": "Terathon Software OpenGEX Exporter",
	"author": "Eric Lengyel",
	"version": (2, 0, 0, 0),
	"blender": (2, 80, 0),
	"location": "File > Import-Export",
	"wiki_url": "http://opengex.org/",
	"category": "Import-Export"}


import bpy
import math
import os
import struct
import time
from enum import Enum
from bpy_extras.io_utils import ExportHelper


kNodeTypeNode = 0
kNodeTypeBone = 1
kNodeTypeGeometry = 2
kNodeTypeLight = 3
kNodeTypeCamera = 4

kAnimationSampled = 0
kAnimationLinear = 1
kAnimationBezier = 2

kExportEpsilon = 1.0e-6


structIdentifier = [B"Node $", B"BoneNode $", B"GeometryNode $", B"LightNode $", B"CameraNode $"]


subtranslationName = [B"xpos", B"ypos", B"zpos"]
subrotationName = [B"xrot", B"yrot", B"zrot"]
subscaleName = [B"xscl", B"yscl", B"zscl"]
deltaSubtranslationName = [B"dxpos", B"dypos", B"dzpos"]
deltaSubrotationName = [B"dxrot", B"dyrot", B"dzrot"]
deltaSubscaleName = [B"dxscl", B"dyscl", B"dzscl"]
axisName = [B"x", B"y", B"z"]

class MaterialPropertyFlags(Enum):
	PropertyColor = 1
	PropertyParam = 2
	PropertySpectrum = 3 # not supported
	PropertyTexture = 4

class ExportVertex:
	__slots__ = ("hash", "vertexIndex", "faceIndex", "position", "normal", "color", "texcoord0", "texcoord1")

	def __init__(self):
		self.color = [1.0, 1.0, 1.0]
		self.texcoord0 = [0.0, 0.0]
		self.texcoord1 = [0.0, 0.0]
		self.normal = [0.0, 0.0, 1.0]

	def __eq__(self, v):
		if (self.hash != v.hash):
			return (False)
		if (self.position != v.position):
			return (False)
		if (self.normal != v.normal):
			return (False)
		if (self.color != v.color):
			return (False)
		if (self.texcoord0 != v.texcoord0):
			return (False)
		if (self.texcoord1 != v.texcoord1):
			return (False)
		return (True)

	def Hash(self):
		h = hash(self.position[0])
		h = h * 21737 + hash(self.position[1])
		h = h * 21737 + hash(self.position[2])
		h = h * 21737 + hash(self.normal[0])
		h = h * 21737 + hash(self.normal[1])
		h = h * 21737 + hash(self.normal[2])
		h = h * 21737 + hash(self.color[0])
		h = h * 21737 + hash(self.color[1])
		h = h * 21737 + hash(self.color[2])
		h = h * 21737 + hash(self.texcoord0[0])
		h = h * 21737 + hash(self.texcoord0[1])
		h = h * 21737 + hash(self.texcoord1[0])
		h = h * 21737 + hash(self.texcoord1[1])
		self.hash = h


class OpenGexExporter(bpy.types.Operator, ExportHelper):
	"""Export to OpenGEX format"""
	bl_idname = "export_scene.ogex"
	bl_label = "Export OpenGEX"
	filename_ext = ".ogex"

	option_export_selection : bpy.props.BoolProperty(name = "Export Selection Only", description = "Export only selected objects", default = False)
	option_sample_animation : bpy.props.BoolProperty(name = "Force Sampled Animation", description = "Always export animation as per-frame samples", default = False)
	option_float_as_hex : bpy.props.BoolProperty(name = "Use Hexadecimals", description = "Decimal numbers will be exported as hexadecimal numbers", default = True)
	option_export_vertex_colors : bpy.props.BoolProperty(name = "Export Vertex Colors", description = "Export the active vertex color layer", default = False)
	option_export_uvs : bpy.props.BoolProperty(name = "Export UVs", description = "Export the active UV layer", default = True)
	option_export_normals : bpy.props.BoolProperty(name = "Export Normals", description = "Export vertex normals", default = True)
	option_export_materials : bpy.props.BoolProperty(name = "Export Materials", description = "Export all materials used in the scene", default = True)

	def Write(self, text):
		self.file.write(text)


	def IndentWrite(self, text, extra = 0, newline = False):
		if (newline):
			self.file.write(B"\n")
		for i in range(self.indentLevel + extra):
			self.file.write(B"\t")
		self.file.write(text)


	def WriteInt(self, i):
		self.file.write(bytes(str(i), "UTF-8"))

	def WriteFloatAsIs(self, f):
		if ((math.isinf(f)) or (math.isnan(f))):
			self.file.write(B"0.0")
		else:
			self.file.write(bytes(str('{:.6f}'.format(f)), "UTF-8"))
	
	def FloatToHex(self, f):
		i = struct.unpack('<I', struct.pack('<f', f))[0]
		return '0x{:08x}'.format(i)

	def WriteFloatAsHex(self, f):
		if ((math.isinf(f)) or (math.isnan(f))):
			self.file.write('0x{:08x}'.format(0.0))
		else:
			self.file.write(bytes(str(self.FloatToHex(f)), "UTF-8"))

	WriteFloatMap = [ WriteFloatAsIs, WriteFloatAsHex ]

	def WriteFloat(self, f):
		self.WriteFloatMap[int(self.option_float_as_hex)](self, f)

	def WriteMatrix(self, matrix):
		self.IndentWrite(B"{", 1)
		self.WriteFloat(matrix[0][0])
		self.Write(B", ")
		self.WriteFloat(matrix[1][0])
		self.Write(B", ")
		self.WriteFloat(matrix[2][0])
		self.Write(B", ")
		self.WriteFloat(matrix[3][0])
		self.Write(B",\n")

		self.IndentWrite(B" ", 1)
		self.WriteFloat(matrix[0][1])
		self.Write(B", ")
		self.WriteFloat(matrix[1][1])
		self.Write(B", ")
		self.WriteFloat(matrix[2][1])
		self.Write(B", ")
		self.WriteFloat(matrix[3][1])
		self.Write(B",\n")

		self.IndentWrite(B" ", 1)
		self.WriteFloat(matrix[0][2])
		self.Write(B", ")
		self.WriteFloat(matrix[1][2])
		self.Write(B", ")
		self.WriteFloat(matrix[2][2])
		self.Write(B", ")
		self.WriteFloat(matrix[3][2])
		self.Write(B",\n")

		self.IndentWrite(B" ", 1)
		self.WriteFloat(matrix[0][3])
		self.Write(B", ")
		self.WriteFloat(matrix[1][3])
		self.Write(B", ")
		self.WriteFloat(matrix[2][3])
		self.Write(B", ")
		self.WriteFloat(matrix[3][3])
		self.Write(B"}\n")


	def WriteMatrixFlat(self, matrix):
		self.IndentWrite(B"{", 1)
		self.WriteFloat(matrix[0][0])
		self.Write(B", ")
		self.WriteFloat(matrix[1][0])
		self.Write(B", ")
		self.WriteFloat(matrix[2][0])
		self.Write(B", ")
		self.WriteFloat(matrix[3][0])
		self.Write(B", ")
		self.WriteFloat(matrix[0][1])
		self.Write(B", ")
		self.WriteFloat(matrix[1][1])
		self.Write(B", ")
		self.WriteFloat(matrix[2][1])
		self.Write(B", ")
		self.WriteFloat(matrix[3][1])
		self.Write(B", ")
		self.WriteFloat(matrix[0][2])
		self.Write(B", ")
		self.WriteFloat(matrix[1][2])
		self.Write(B", ")
		self.WriteFloat(matrix[2][2])
		self.Write(B", ")
		self.WriteFloat(matrix[3][2])
		self.Write(B", ")
		self.WriteFloat(matrix[0][3])
		self.Write(B", ")
		self.WriteFloat(matrix[1][3])
		self.Write(B", ")
		self.WriteFloat(matrix[2][3])
		self.Write(B", ")
		self.WriteFloat(matrix[3][3])
		self.Write(B"}")


	def WriteColor(self, color):
		self.Write(B"{")
		self.WriteFloat(color[0])
		self.Write(B", ")
		self.WriteFloat(color[1])
		self.Write(B", ")
		self.WriteFloat(color[2])
		self.Write(B"}")


	def WriteFileName(self, filename):
		length = len(filename)
		if (length != 0):
			if ((length > 2) and (filename[1] == ":")):
				self.Write(B"//")
				self.Write(bytes(filename[0], "UTF-8"))
				self.Write(bytes(filename[2:length].replace("\\", "/"), "UTF-8"))
			else:
				self.Write(bytes(filename.replace("\\", "/"), "UTF-8"))


	def WriteIntArray(self, valueArray):
		count = len(valueArray)
		k = 0

		lineCount = count >> 6
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(63):
				self.WriteInt(valueArray[k])
				self.Write(B", ")
				k += 1

			self.WriteInt(valueArray[k])
			k += 1

			if (i * 64 < count - 64):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 63
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteInt(valueArray[k])
				self.Write(B", ")
				k += 1

			self.WriteInt(valueArray[k])
			self.Write(B"\n")


	def WriteFloatArray(self, valueArray):
		count = len(valueArray)
		k = 0

		lineCount = count >> 4
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(15):
				self.WriteFloat(valueArray[k])
				self.Write(B", ")
				k += 1

			self.WriteFloat(valueArray[k])
			k += 1

			if (i * 16 < count - 16):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 15
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteFloat(valueArray[k])
				self.Write(B", ")
				k += 1

			self.WriteFloat(valueArray[k])
			self.Write(B"\n")


	def WriteVector2D(self, vector):
		self.Write(B"{")
		self.WriteFloat(vector[0])
		self.Write(B", ")
		self.WriteFloat(vector[1])
		self.Write(B"}")


	def WriteVector3D(self, vector):
		self.Write(B"{")
		self.WriteFloat(vector[0])
		self.Write(B", ")
		self.WriteFloat(vector[1])
		self.Write(B", ")
		self.WriteFloat(vector[2])
		self.Write(B"}")


	def WriteVector4D(self, vector):
		self.Write(B"{")
		self.WriteFloat(vector[0])
		self.Write(B", ")
		self.WriteFloat(vector[1])
		self.Write(B", ")
		self.WriteFloat(vector[2])
		self.Write(B", ")
		self.WriteFloat(vector[3])
		self.Write(B"}")


	def WriteQuaternion(self, quaternion):
		self.Write(B"{")
		self.WriteFloat(quaternion[1])
		self.Write(B", ")
		self.WriteFloat(quaternion[2])
		self.Write(B", ")
		self.WriteFloat(quaternion[3])
		self.Write(B", ")
		self.WriteFloat(quaternion[0])
		self.Write(B"}")


	def WriteVertexArray2D(self, vertexArray, attrib):
		count = len(vertexArray)
		k = 0

		lineCount = count >> 3
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(7):
				self.WriteVector2D(getattr(vertexArray[k], attrib))
				self.Write(B", ")
				k += 1

			self.WriteVector2D(getattr(vertexArray[k], attrib))
			k += 1

			if (i * 8 < count - 8):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 7
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteVector2D(getattr(vertexArray[k], attrib))
				self.Write(B", ")
				k += 1

			self.WriteVector2D(getattr(vertexArray[k], attrib))
			self.Write(B"\n")


	def WriteVertexArray3D(self, vertexArray, attrib):
		count = len(vertexArray)
		k = 0

		lineCount = count >> 3
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(7):
				self.WriteVector3D(getattr(vertexArray[k], attrib))
				self.Write(B", ")
				k += 1

			self.WriteVector3D(getattr(vertexArray[k], attrib))
			k += 1

			if (i * 8 < count - 8):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 7
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteVector3D(getattr(vertexArray[k], attrib))
				self.Write(B", ")
				k += 1

			self.WriteVector3D(getattr(vertexArray[k], attrib))
			self.Write(B"\n")


	def WriteMorphPositionArray3D(self, vertexArray, meshVertexArray):
		count = len(vertexArray)
		k = 0

		lineCount = count >> 3
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(7):
				self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].co)
				self.Write(B", ")
				k += 1

			self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].co)
			k += 1

			if (i * 8 < count - 8):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 7
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].co)
				self.Write(B", ")
				k += 1

			self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].co)
			self.Write(B"\n")


	def WriteMorphNormalArray3D(self, vertexArray, meshVertexArray, tessFaceArray):
		count = len(vertexArray)
		k = 0

		lineCount = count >> 3
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(7):
				face = tessFaceArray[vertexArray[k].faceIndex]
				self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].normal if (face.use_smooth) else face.normal)
				self.Write(B", ")
				k += 1

			face = tessFaceArray[vertexArray[k].faceIndex]
			self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].normal if (face.use_smooth) else face.normal)
			k += 1

			if (i * 8 < count - 8):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 7
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				face = tessFaceArray[vertexArray[k].faceIndex]
				self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].normal if (face.use_smooth) else face.normal)
				self.Write(B", ")
				k += 1

			face = tessFaceArray[vertexArray[k].faceIndex]
			self.WriteVector3D(meshVertexArray[vertexArray[k].vertexIndex].normal if (face.use_smooth) else face.normal)
			self.Write(B"\n")


	def WriteTriangle(self, triangleIndex, indexTable):
		i = triangleIndex * 3
		self.Write(B"{")
		self.WriteInt(indexTable[i])
		self.Write(B", ")
		self.WriteInt(indexTable[i + 1])
		self.Write(B", ")
		self.WriteInt(indexTable[i + 2])
		self.Write(B"}")


	def WriteTriangleArray(self, count, indexTable):
		triangleIndex = 0

		lineCount = count >> 4
		for i in range(lineCount):
			self.IndentWrite(B"", 1)
			for j in range(15):
				self.WriteTriangle(triangleIndex, indexTable)
				self.Write(B", ")
				triangleIndex += 1

			self.WriteTriangle(triangleIndex, indexTable)
			triangleIndex += 1

			if (i * 16 < count - 16):
				self.Write(B",\n")
			else:
				self.Write(B"\n")

		count &= 15
		if (count != 0):
			self.IndentWrite(B"", 1)
			for j in range(count - 1):
				self.WriteTriangle(triangleIndex, indexTable)
				self.Write(B", ")
				triangleIndex += 1

			self.WriteTriangle(triangleIndex, indexTable)
			self.Write(B"\n")


	def WriteNodeTable(self, objectRef):
		first = True
		for node in objectRef[1]["nodeTable"]:
			if (first):
				self.Write(B"\t\t// ")
			else:
				self.Write(B", ")
			self.Write(bytes(node.name, "UTF-8"))
			first = False


	@staticmethod
	def GetNodeType(node):
		if (node.type == "MESH"):
			if (len(node.data.polygons) != 0):
				return (kNodeTypeGeometry)
		elif (node.type == "LIGHT"):
			type = node.data.type
			if ((type == "SUN") or (type == "POINT") or (type == "SPOT")): # @TODO Add support for area lights. "AREA"
				return (kNodeTypeLight)
		elif (node.type == "CAMERA"):
			return (kNodeTypeCamera)

		return (kNodeTypeNode)


	@staticmethod
	def GetShapeKeys(mesh):
		shapeKeys = mesh.shape_keys
		if ((shapeKeys) and (len(shapeKeys.key_blocks) > 1)):
			return (shapeKeys)

		return (None)


	def FindNode(self, name):
		for nodeRef in self.nodeArray.items():
			if (nodeRef[0].name == name):
				return (nodeRef)
		return (None)


	@staticmethod
	def DeindexMesh(mesh, materialTable, shouldExportVertexColor = True):

		mesh.calc_loop_triangles()
		mesh.calc_normals_split()
		
		# This function deindexes all vertex positions, colors, and texcoords.
		# Three separate ExportVertex structures are created for each triangle.

		vertexArray = mesh.vertices
		exportVertexArray = []
		faceIndex = 0

		for face in mesh.loop_triangles:
			k1 = face.vertices[0]
			k2 = face.vertices[1]
			k3 = face.vertices[2]

			v1 = vertexArray[k1]
			v2 = vertexArray[k2]
			v3 = vertexArray[k3]

			exportVertex = ExportVertex()
			exportVertex.vertexIndex = k1
			exportVertex.faceIndex = faceIndex
			exportVertex.position = v1.co
			if face.use_smooth:
				exportVertex.normal[0] = face.split_normals[0][0]
				exportVertex.normal[1] = face.split_normals[0][1]
				exportVertex.normal[2] = face.split_normals[0][2]
			else:
				exportVertex.normal = face.normal

			exportVertexArray.append(exportVertex)

			exportVertex = ExportVertex()
			exportVertex.vertexIndex = k2
			exportVertex.faceIndex = faceIndex
			exportVertex.position = v2.co
			if face.use_smooth:
				exportVertex.normal[0] = face.split_normals[1][0]
				exportVertex.normal[1] = face.split_normals[1][1]
				exportVertex.normal[2] = face.split_normals[1][2]
			else:
				exportVertex.normal = face.normal

			exportVertexArray.append(exportVertex)

			exportVertex = ExportVertex()
			exportVertex.vertexIndex = k3
			exportVertex.faceIndex = faceIndex
			exportVertex.position = v3.co
			if face.use_smooth:
				exportVertex.normal[0] = face.split_normals[2][0]
				exportVertex.normal[1] = face.split_normals[2][1]
				exportVertex.normal[2] = face.split_normals[2][2]
			else:
				exportVertex.normal = face.normal

			exportVertexArray.append(exportVertex)

			materialTable.append(face.material_index)

			faceIndex += 1

		colorCount = len(mesh.vertex_colors)
		if (colorCount > 0 and shouldExportVertexColor):
			colorFace = mesh.vertex_colors[0].data
			vertexIndex = 0
			faceIndex = 0

			for face in mesh.loop_triangles:
				cf = colorFace[faceIndex]
				exportVertexArray[vertexIndex].color[0] = cf.color[0]
				vertexIndex += 1
				exportVertexArray[vertexIndex].color[1] = cf.color[1]
				vertexIndex += 1
				exportVertexArray[vertexIndex].color[2] = cf.color[2]
				vertexIndex += 1

				if (len(face.vertices) == 4):
					exportVertexArray[vertexIndex].color[0] = cf.color[1]
					vertexIndex += 1
					exportVertexArray[vertexIndex].color[1] = cf.color[2]
					vertexIndex += 1
					exportVertexArray[vertexIndex].color[2] = cf.color[3]
					vertexIndex += 1

				faceIndex += 1

		uv_layer0 = mesh.uv_layers[0] if len(mesh.uv_layers) > 0 else None
		uv_layer1 = mesh.uv_layers[1] if len(mesh.uv_layers) > 1 else None

		vertexIndex = 0
		for tri in mesh.loop_triangles:
			for loop_index in tri.loops:

				if uv_layer0:
					uv0 = uv_layer0.data[loop_index].uv
					exportVertexArray[vertexIndex].texcoord0 = uv0

				if uv_layer1:
					uv1 = uv_layer1.data[loop_index].uv
					exportVertexArray[vertexIndex].texcoord1 = uv1

				vertexIndex += 1

		for ev in exportVertexArray:
			ev.Hash()

		return (exportVertexArray)


	@staticmethod
	def FindExportVertex(bucket, exportVertexArray, vertex):
		for index in bucket:
			if (exportVertexArray[index] == vertex):
				return (index)

		return (-1)


	@staticmethod
	def UnifyVertices(exportVertexArray, indexTable):

		# This function looks for identical vertices having exactly the same position, normal,
		# color, and texcoords. Duplicate vertices are unified, and a new index table is returned.

		bucketCount = len(exportVertexArray) >> 3
		if (bucketCount > 1):

			# Round down to nearest power of two.

			while True:
				count = bucketCount & (bucketCount - 1)
				if (count == 0):
					break
				bucketCount = count
		else:
			bucketCount = 1

		hashTable = [[] for i in range(bucketCount)]
		unifiedVertexArray = []

		print("Export Vertex Array %d" % len(exportVertexArray))

		for i in range(len(exportVertexArray)):
			ev = exportVertexArray[i]
			bucket = ev.hash & (bucketCount - 1)
			index = OpenGexExporter.FindExportVertex(hashTable[bucket], exportVertexArray, ev)
			if (index < 0):
				indexTable.append(len(unifiedVertexArray))
				unifiedVertexArray.append(ev)
				hashTable[bucket].append(i)
			else:
				indexTable.append(indexTable[index])

		print("Unified vertex array %d" % len(unifiedVertexArray))

		return (unifiedVertexArray)


	def ProcessBone(self, bone):
		if ((self.exportAllFlag) or (bone.select)):
			self.nodeArray[bone] = {"nodeType" : kNodeTypeBone, "structName" : bytes("node" + str(len(self.nodeArray) + 1), "UTF-8")}

		for subnode in bone.children:
			self.ProcessBone(subnode)


	def ProcessNode(self, node):
		if ((self.exportAllFlag) or (node.select_get())):
			type = OpenGexExporter.GetNodeType(node)
			self.nodeArray[node] = {"nodeType" : type, "structName" : bytes("node" + str(len(self.nodeArray) + 1), "UTF-8")}

			if (node.parent_type == "BONE"):
				boneSubnodeArray = self.boneParentArray.get(node.parent_bone)
				if (boneSubnodeArray):
					boneSubnodeArray.append(node)
				else:
					self.boneParentArray[node.parent_bone] = [node]

			if (node.type == "ARMATURE"):
				skeleton = node.data
				if (skeleton):
					for bone in skeleton.bones:
						if (not bone.parent):
							self.ProcessBone(bone)

		for subnode in node.children:
			self.ProcessNode(subnode)


	def ProcessSkinnedMeshes(self):
		for nodeRef in self.nodeArray.items():
			if (nodeRef[1]["nodeType"] == kNodeTypeGeometry):
				armature = nodeRef[0].find_armature()
				if (armature):
					for bone in armature.data.bones:
						boneRef = self.FindNode(bone.name)
						if (boneRef):

							# If a node is used as a bone, then we force its type to be a bone.

							boneRef[1]["nodeType"] = kNodeTypeBone


	@staticmethod
	def ClassifyAnimationCurve(fcurve):
		linearCount = 0
		bezierCount = 0

		for key in fcurve.keyframe_points:
			interp = key.interpolation
			if (interp == "LINEAR"):
				linearCount += 1
			elif (interp == "BEZIER"):
				bezierCount += 1
			else:
				return (kAnimationSampled)

		if (bezierCount == 0):
			return (kAnimationLinear)
		elif (linearCount == 0):
			return (kAnimationBezier)
			
		return (kAnimationSampled)


	@staticmethod
	def AnimationKeysDifferent(fcurve):
		keyCount = len(fcurve.keyframe_points)
		if (keyCount > 0):
			key1 = fcurve.keyframe_points[0].co[1]

			for i in range(1, keyCount):
				key2 = fcurve.keyframe_points[i].co[1]
				if (math.fabs(key2 - key1) > kExportEpsilon):
					return (True)

		return (False)


	@staticmethod
	def AnimationTangentsNonzero(fcurve):
		keyCount = len(fcurve.keyframe_points)
		if (keyCount > 0):
			key = fcurve.keyframe_points[0].co[1]
			left = fcurve.keyframe_points[0].handle_left[1]
			right = fcurve.keyframe_points[0].handle_right[1]
			if ((math.fabs(key - left) > kExportEpsilon) or (math.fabs(right - key) > kExportEpsilon)):
				return (True)

			for i in range(1, keyCount):
				key = fcurve.keyframe_points[i].co[1]
				left = fcurve.keyframe_points[i].handle_left[1]
				right = fcurve.keyframe_points[i].handle_right[1]
				if ((math.fabs(key - left) > kExportEpsilon) or (math.fabs(right - key) > kExportEpsilon)):
					return (True)

		return (False)


	@staticmethod
	def AnimationPresent(fcurve, kind):
		if (kind != kAnimationBezier):
			return (OpenGexExporter.AnimationKeysDifferent(fcurve))

		return ((OpenGexExporter.AnimationKeysDifferent(fcurve)) or (OpenGexExporter.AnimationTangentsNonzero(fcurve)))


	@staticmethod
	def MatricesDifferent(m1, m2):
		for i in range(4):
			for j in range(4):
				if (math.fabs(m1[i][j] - m2[i][j]) > kExportEpsilon):
					return (True)

		return (False)


	@staticmethod
	def CollectBoneAnimation(armature, name):
		path = "pose.bones[\"" + name + "\"]."
		curveArray = []

		if (armature.animation_data):
			action = armature.animation_data.action
			if (action):
				for fcurve in action.fcurves:
					if (fcurve.data_path.startswith(path)):
						curveArray.append(fcurve)

		return (curveArray)


	def ExportKeyTimes(self, fcurve):
		self.IndentWrite(B"Key {float {")

		keyCount = len(fcurve.keyframe_points)
		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			time = fcurve.keyframe_points[i].co[0] - self.beginFrame
			self.WriteFloat(time * self.frameTime)

		self.Write(B"}}\n")


	def ExportKeyTimeControlPoints(self, fcurve):
		self.IndentWrite(B"Key (kind = \"-control\") {float {")

		keyCount = len(fcurve.keyframe_points)
		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			ctrl = fcurve.keyframe_points[i].handle_left[0] - self.beginFrame
			self.WriteFloat(ctrl * self.frameTime)

		self.Write(B"}}\n")
		self.IndentWrite(B"Key (kind = \"+control\") {float {")

		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			ctrl = fcurve.keyframe_points[i].handle_right[0] - self.beginFrame
			self.WriteFloat(ctrl * self.frameTime)

		self.Write(B"}}\n")


	def ExportKeyValues(self, fcurve):
		self.IndentWrite(B"Key {float {")

		keyCount = len(fcurve.keyframe_points)
		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			value = fcurve.keyframe_points[i].co[1]
			self.WriteFloat(value)

		self.Write(B"}}\n")


	def ExportKeyValueControlPoints(self, fcurve):
		self.IndentWrite(B"Key (kind = \"-control\") {float {")

		keyCount = len(fcurve.keyframe_points)
		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			ctrl = fcurve.keyframe_points[i].handle_left[1]
			self.WriteFloat(ctrl)

		self.Write(B"}}\n")
		self.IndentWrite(B"Key (kind = \"+control\") {float {")

		for i in range(keyCount):
			if (i > 0):
				self.Write(B", ")

			ctrl = fcurve.keyframe_points[i].handle_right[1]
			self.WriteFloat(ctrl)

		self.Write(B"}}\n")


	def ExportAnimationTrack(self, fcurve, kind, target, newline):

		# This function exports a single animation track. The curve types for the
		# Time and Value structures are given by the kind parameter.

		self.IndentWrite(B"Track (target = %", 0, newline)
		self.Write(target)
		self.Write(B")\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		if (kind != kAnimationBezier):
			self.IndentWrite(B"Time\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.ExportKeyTimes(fcurve)

			self.IndentWrite(B"}\n\n", -1)
			self.IndentWrite(B"Value\n", -1)
			self.IndentWrite(B"{\n", -1)

			self.ExportKeyValues(fcurve)

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		else:
			self.IndentWrite(B"Time (curve = \"bezier\")\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.ExportKeyTimes(fcurve)
			self.ExportKeyTimeControlPoints(fcurve)

			self.IndentWrite(B"}\n\n", -1)
			self.IndentWrite(B"Value (curve = \"bezier\")\n", -1)
			self.IndentWrite(B"{\n", -1)

			self.ExportKeyValues(fcurve)
			self.ExportKeyValueControlPoints(fcurve)

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")


	def ExportNodeSampledAnimation(self, node, scene):

		# This function exports animation as full 4x4 matrices for each frame.

		currentFrame = scene.frame_current
		currentSubframe = scene.frame_subframe

		animationFlag = False
		m1 = node.matrix_local.copy()

		for i in range(self.beginFrame, self.endFrame):
			scene.frame_set(i)
			m2 = node.matrix_local
			if (OpenGexExporter.MatricesDifferent(m1, m2)):
				animationFlag = True
				break

		if (animationFlag):
			self.IndentWrite(B"Animation\n", 0, True)
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Track (target = %transform)\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Time\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Key {float {")

			for i in range(self.beginFrame, self.endFrame):
				self.WriteFloat((i - self.beginFrame) * self.frameTime)
				self.Write(B", ")

			self.WriteFloat(self.endFrame * self.frameTime)
			self.Write(B"}}\n")

			self.IndentWrite(B"}\n\n", -1)
			self.IndentWrite(B"Value\n", -1)
			self.IndentWrite(B"{\n", -1)

			self.IndentWrite(B"Key\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"float[16]\n")
			self.IndentWrite(B"{\n")

			for i in range(self.beginFrame, self.endFrame):
				scene.frame_set(i)
				self.WriteMatrixFlat(node.matrix_local)
				self.Write(B",\n")

			scene.frame_set(self.endFrame)
			self.WriteMatrixFlat(node.matrix_local)
			self.IndentWrite(B"}\n", 0, True)

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		scene.frame_set(currentFrame, subframe = currentSubframe)


	def ExportBoneSampledAnimation(self, poseBone, scene):

		# This function exports bone animation as full 4x4 matrices for each frame.

		currentFrame = scene.frame_current
		currentSubframe = scene.frame_subframe

		animationFlag = False
		m1 = poseBone.matrix.copy()

		for i in range(self.beginFrame, self.endFrame):
			scene.frame_set(i)
			m2 = poseBone.matrix
			if (OpenGexExporter.MatricesDifferent(m1, m2)):
				animationFlag = True
				break

		if (animationFlag):
			self.IndentWrite(B"Animation\n", 0, True)
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Track (target = %transform)\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Time\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"Key {float {")

			for i in range(self.beginFrame, self.endFrame):
				self.WriteFloat((i - self.beginFrame) * self.frameTime)
				self.Write(B", ")

			self.WriteFloat(self.endFrame * self.frameTime)
			self.Write(B"}}\n")

			self.IndentWrite(B"}\n\n", -1)
			self.IndentWrite(B"Value\n", -1)
			self.IndentWrite(B"{\n", -1)

			self.IndentWrite(B"Key\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"float[16]\n")
			self.IndentWrite(B"{\n")

			parent = poseBone.parent
			if (parent):
				for i in range(self.beginFrame, self.endFrame):
					scene.frame_set(i)
					if (math.fabs(parent.matrix.determinant()) > kExportEpsilon):
						self.WriteMatrixFlat(parent.matrix.inverted() * poseBone.matrix)
					else:
						self.WriteMatrixFlat(poseBone.matrix)

					self.Write(B",\n")

				scene.frame_set(self.endFrame)
				if (math.fabs(parent.matrix.determinant()) > kExportEpsilon):
					self.WriteMatrixFlat(parent.matrix.inverted() * poseBone.matrix)
				else:
					self.WriteMatrixFlat(poseBone.matrix)

				self.IndentWrite(B"}\n", 0, True)

			else:
				for i in range(self.beginFrame, self.endFrame):
					scene.frame_set(i)
					self.WriteMatrixFlat(poseBone.matrix)
					self.Write(B",\n")

				scene.frame_set(self.endFrame)
				self.WriteMatrixFlat(poseBone.matrix)
				self.IndentWrite(B"}\n", 0, True)

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		scene.frame_set(currentFrame, subframe = currentSubframe)


	def ExportMorphWeightSampledAnimationTrack(self, block, target, scene, newline):
		currentFrame = scene.frame_current
		currentSubframe = scene.frame_subframe

		self.IndentWrite(B"Track (target = %", 0, newline)
		self.Write(target)
		self.Write(B")\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"Time\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"Key {float {")

		for i in range(self.beginFrame, self.endFrame):
			self.WriteFloat((i - self.beginFrame) * self.frameTime)
			self.Write(B", ")

		self.WriteFloat(self.endFrame * self.frameTime)
		self.Write(B"}}\n")

		self.IndentWrite(B"}\n\n", -1)
		self.IndentWrite(B"Value\n", -1)
		self.IndentWrite(B"{\n", -1)

		self.IndentWrite(B"Key {float {")

		for i in range(self.beginFrame, self.endFrame):
			scene.frame_set(i)
			self.WriteFloat(block.value)
			self.Write(B", ")

		scene.frame_set(self.endFrame)
		self.WriteFloat(block.value)
		self.Write(B"}}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		scene.frame_set(currentFrame, subframe = currentSubframe)


	def ExportNodeTransform(self, node, scene):
		posAnimCurve = [None, None, None]
		rotAnimCurve = [None, None, None]
		sclAnimCurve = [None, None, None]
		posAnimKind = [0, 0, 0]
		rotAnimKind = [0, 0, 0]
		sclAnimKind = [0, 0, 0]

		deltaPosAnimCurve = [None, None, None]
		deltaRotAnimCurve = [None, None, None]
		deltaSclAnimCurve = [None, None, None]
		deltaPosAnimKind = [0, 0, 0]
		deltaRotAnimKind = [0, 0, 0]
		deltaSclAnimKind = [0, 0, 0]

		positionAnimated = False
		rotationAnimated = False
		scaleAnimated = False
		posAnimated = [False, False, False]
		rotAnimated = [False, False, False]
		sclAnimated = [False, False, False]

		deltaPositionAnimated = False
		deltaRotationAnimated = False
		deltaScaleAnimated = False
		deltaPosAnimated = [False, False, False]
		deltaRotAnimated = [False, False, False]
		deltaSclAnimated = [False, False, False]

		mode = node.rotation_mode
		sampledAnimation = ((self.sampleAnimationFlag) or (mode == "QUATERNION") or (mode == "AXIS_ANGLE"))

		if ((not sampledAnimation) and (node.animation_data)):
			action = node.animation_data.action
			if (action):
				for fcurve in action.fcurves:
					kind = OpenGexExporter.ClassifyAnimationCurve(fcurve)
					if (kind != kAnimationSampled):
						if (fcurve.data_path == "location"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not posAnimCurve[i])):
									posAnimCurve[i] = fcurve
									posAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										posAnimated[i] = True
						elif (fcurve.data_path == "delta_location"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not deltaPosAnimCurve[i])):
									deltaPosAnimCurve[i] = fcurve
									deltaPosAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										deltaPosAnimated[i] = True
						elif (fcurve.data_path == "rotation_euler"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not rotAnimCurve[i])):
									rotAnimCurve[i] = fcurve
									rotAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										rotAnimated[i] = True
						elif (fcurve.data_path == "delta_rotation_euler"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not deltaRotAnimCurve[i])):
									deltaRotAnimCurve[i] = fcurve
									deltaRotAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										deltaRotAnimated[i] = True
						elif (fcurve.data_path == "scale"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not sclAnimCurve[i])):
									sclAnimCurve[i] = fcurve
									sclAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										sclAnimated[i] = True
						elif (fcurve.data_path == "delta_scale"):
							for i in range(3):
								if ((fcurve.array_index == i) and (not deltaSclAnimCurve[i])):
									deltaSclAnimCurve[i] = fcurve
									deltaSclAnimKind[i] = kind
									if (OpenGexExporter.AnimationPresent(fcurve, kind)):
										deltaSclAnimated[i] = True
						elif ((fcurve.data_path == "rotation_axis_angle") or (fcurve.data_path == "rotation_quaternion") or (fcurve.data_path == "delta_rotation_quaternion")):
							sampledAnimation = True
							break
					else:
						sampledAnimation = True
						break

		positionAnimated = posAnimated[0] | posAnimated[1] | posAnimated[2]
		rotationAnimated = rotAnimated[0] | rotAnimated[1] | rotAnimated[2]
		scaleAnimated = sclAnimated[0] | sclAnimated[1] | sclAnimated[2]

		deltaPositionAnimated = deltaPosAnimated[0] | deltaPosAnimated[1] | deltaPosAnimated[2]
		deltaRotationAnimated = deltaRotAnimated[0] | deltaRotAnimated[1] | deltaRotAnimated[2]
		deltaScaleAnimated = deltaSclAnimated[0] | deltaSclAnimated[1] | deltaSclAnimated[2]

		if ((sampledAnimation) or ((not positionAnimated) and (not rotationAnimated) and (not scaleAnimated) and (not deltaPositionAnimated) and (not deltaRotationAnimated) and (not deltaScaleAnimated))):

			# If there's no keyframe animation at all, then write the node transform as a single 4x4 matrix.
			# We might still be exporting sampled animation below.

			self.IndentWrite(B"Transform")

			if (sampledAnimation):
				self.Write(B" %transform")

			self.IndentWrite(B"{\n", 0, True)
			self.indentLevel += 1

			self.IndentWrite(B"float[16]\n")
			self.IndentWrite(B"{\n")
			self.WriteMatrix(node.matrix_local)
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

			if (sampledAnimation):
				self.ExportNodeSampledAnimation(node, scene)

		else:
			structFlag = False

			deltaTranslation = node.delta_location
			if (deltaPositionAnimated):

				# When the delta location is animated, write the x, y, and z components separately
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					pos = deltaTranslation[i]
					if ((deltaPosAnimated[i]) or (math.fabs(pos) > kExportEpsilon)):
						self.IndentWrite(B"Translation %", 0, structFlag)
						self.Write(deltaSubtranslationName[i])
						self.Write(B" (kind = \"")
						self.Write(axisName[i])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(pos)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			elif ((math.fabs(deltaTranslation[0]) > kExportEpsilon) or (math.fabs(deltaTranslation[1]) > kExportEpsilon) or (math.fabs(deltaTranslation[2]) > kExportEpsilon)):
				self.IndentWrite(B"Translation\n")
				self.IndentWrite(B"{\n")
				self.IndentWrite(B"float[3] {", 1)
				self.WriteVector3D(deltaTranslation)
				self.Write(B"}")
				self.IndentWrite(B"}\n", 0, True)

				structFlag = True

			translation = node.location
			if (positionAnimated):

				# When the location is animated, write the x, y, and z components separately
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					pos = translation[i]
					if ((posAnimated[i]) or (math.fabs(pos) > kExportEpsilon)):
						self.IndentWrite(B"Translation %", 0, structFlag)
						self.Write(subtranslationName[i])
						self.Write(B" (kind = \"")
						self.Write(axisName[i])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(pos)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			elif ((math.fabs(translation[0]) > kExportEpsilon) or (math.fabs(translation[1]) > kExportEpsilon) or (math.fabs(translation[2]) > kExportEpsilon)):
				self.IndentWrite(B"Translation\n")
				self.IndentWrite(B"{\n")
				self.IndentWrite(B"float[3] {", 1)
				self.WriteVector3D(translation)
				self.Write(B"}")
				self.IndentWrite(B"}\n", 0, True)

				structFlag = True

			if (deltaRotationAnimated):

				# When the delta rotation is animated, write three separate Euler angle rotations
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					axis = ord(mode[2 - i]) - 0x58
					angle = node.delta_rotation_euler[axis]
					if ((deltaRotAnimated[axis]) or (math.fabs(angle) > kExportEpsilon)):
						self.IndentWrite(B"Rotation %", 0, structFlag)
						self.Write(deltaSubrotationName[axis])
						self.Write(B" (kind = \"")
						self.Write(axisName[axis])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(angle)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			else:

				# When the delta rotation is not animated, write it in the representation given by
				# the node's current rotation mode. (There is no axis-angle delta rotation.)

				if (mode == "QUATERNION"):
					quaternion = node.delta_rotation_quaternion
					if ((math.fabs(quaternion[0] - 1.0) > kExportEpsilon) or (math.fabs(quaternion[1]) > kExportEpsilon) or (math.fabs(quaternion[2]) > kExportEpsilon) or (math.fabs(quaternion[3]) > kExportEpsilon)):
						self.IndentWrite(B"Rotation (kind = \"quaternion\")\n", 0, structFlag)
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float[4] {", 1)
						self.WriteQuaternion(quaternion)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

				else:
					for i in range(3):
						axis = ord(mode[2 - i]) - 0x58
						angle = node.delta_rotation_euler[axis]
						if (math.fabs(angle) > kExportEpsilon):
							self.IndentWrite(B"Rotation (kind = \"", 0, structFlag)
							self.Write(axisName[axis])
							self.Write(B"\")\n")
							self.IndentWrite(B"{\n")
							self.IndentWrite(B"float {", 1)
							self.WriteFloat(angle)
							self.Write(B"}")
							self.IndentWrite(B"}\n", 0, True)

							structFlag = True

			if (rotationAnimated):

				# When the rotation is animated, write three separate Euler angle rotations
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					axis = ord(mode[2 - i]) - 0x58
					angle = node.rotation_euler[axis]
					if ((rotAnimated[axis]) or (math.fabs(angle) > kExportEpsilon)):
						self.IndentWrite(B"Rotation %", 0, structFlag)
						self.Write(subrotationName[axis])
						self.Write(B" (kind = \"")
						self.Write(axisName[axis])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(angle)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			else:

				# When the rotation is not animated, write it in the representation given by
				# the node's current rotation mode.

				if (mode == "QUATERNION"):
					quaternion = node.rotation_quaternion
					if ((math.fabs(quaternion[0] - 1.0) > kExportEpsilon) or (math.fabs(quaternion[1]) > kExportEpsilon) or (math.fabs(quaternion[2]) > kExportEpsilon) or (math.fabs(quaternion[3]) > kExportEpsilon)):
						self.IndentWrite(B"Rotation (kind = \"quaternion\")\n", 0, structFlag)
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float[4] {", 1)
						self.WriteQuaternion(quaternion)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

				elif (mode == "AXIS_ANGLE"):
					if (math.fabs(node.rotation_axis_angle[0]) > kExportEpsilon):
						self.IndentWrite(B"Rotation (kind = \"axis\")\n", 0, structFlag)
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float[4] {", 1)
						self.WriteVector4D(node.rotation_axis_angle)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

				else:
					for i in range(3):
						axis = ord(mode[2 - i]) - 0x58
						angle = node.rotation_euler[axis]
						if (math.fabs(angle) > kExportEpsilon):
							self.IndentWrite(B"Rotation (kind = \"", 0, structFlag)
							self.Write(axisName[axis])
							self.Write(B"\")\n")
							self.IndentWrite(B"{\n")
							self.IndentWrite(B"float {", 1)
							self.WriteFloat(angle)
							self.Write(B"}")
							self.IndentWrite(B"}\n", 0, True)

							structFlag = True

			deltaScale = node.delta_scale
			if (deltaScaleAnimated):

				# When the delta scale is animated, write the x, y, and z components separately
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					scl = deltaScale[i]
					if ((deltaSclAnimated[i]) or (math.fabs(scl) > kExportEpsilon)):
						self.IndentWrite(B"Scale %", 0, structFlag)
						self.Write(deltaSubscaleName[i])
						self.Write(B" (kind = \"")
						self.Write(axisName[i])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(scl)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			elif ((math.fabs(deltaScale[0] - 1.0) > kExportEpsilon) or (math.fabs(deltaScale[1] - 1.0) > kExportEpsilon) or (math.fabs(deltaScale[2] - 1.0) > kExportEpsilon)):
				self.IndentWrite(B"Scale\n", 0, structFlag)
				self.IndentWrite(B"{\n")
				self.IndentWrite(B"float[3] {", 1)
				self.WriteVector3D(deltaScale)
				self.Write(B"}")
				self.IndentWrite(B"}\n", 0, True)

				structFlag = True

			scale = node.scale
			if (scaleAnimated):

				# When the scale is animated, write the x, y, and z components separately
				# so they can be targeted by different tracks having different sets of keys.

				for i in range(3):
					scl = scale[i]
					if ((sclAnimated[i]) or (math.fabs(scl) > kExportEpsilon)):
						self.IndentWrite(B"Scale %", 0, structFlag)
						self.Write(subscaleName[i])
						self.Write(B" (kind = \"")
						self.Write(axisName[i])
						self.Write(B"\")\n")
						self.IndentWrite(B"{\n")
						self.IndentWrite(B"float {", 1)
						self.WriteFloat(scl)
						self.Write(B"}")
						self.IndentWrite(B"}\n", 0, True)

						structFlag = True

			elif ((math.fabs(scale[0] - 1.0) > kExportEpsilon) or (math.fabs(scale[1] - 1.0) > kExportEpsilon) or (math.fabs(scale[2] - 1.0) > kExportEpsilon)):
				self.IndentWrite(B"Scale\n", 0, structFlag)
				self.IndentWrite(B"{\n")
				self.IndentWrite(B"float[3] {", 1)
				self.WriteVector3D(scale)
				self.Write(B"}")
				self.IndentWrite(B"}\n", 0, True)

				structFlag = True

			# Export the animation tracks.

			self.IndentWrite(B"Animation (begin = ", 0, True)
			self.WriteFloat((action.frame_range[0] - self.beginFrame) * self.frameTime)
			self.Write(B", end = ")
			self.WriteFloat((action.frame_range[1] - self.beginFrame) * self.frameTime)
			self.Write(B")\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			structFlag = False

			if (positionAnimated):
				for i in range(3):
					if (posAnimated[i]):
						self.ExportAnimationTrack(posAnimCurve[i], posAnimKind[i], subtranslationName[i], structFlag)
						structFlag = True

			if (rotationAnimated):
				for i in range(3):
					if (rotAnimated[i]):
						self.ExportAnimationTrack(rotAnimCurve[i], rotAnimKind[i], subrotationName[i], structFlag)
						structFlag = True

			if (scaleAnimated):
				for i in range(3):
					if (sclAnimated[i]):
						self.ExportAnimationTrack(sclAnimCurve[i], sclAnimKind[i], subscaleName[i], structFlag)
						structFlag = True

			if (deltaPositionAnimated):
				for i in range(3):
					if (deltaPosAnimated[i]):
						self.ExportAnimationTrack(deltaPosAnimCurve[i], deltaPosAnimKind[i], deltaSubtranslationName[i], structFlag)
						structFlag = True

			if (deltaRotationAnimated):
				for i in range(3):
					if (deltaRotAnimated[i]):
						self.ExportAnimationTrack(deltaRotAnimCurve[i], deltaRotAnimKind[i], deltaSubrotationName[i], structFlag)
						structFlag = True

			if (deltaScaleAnimated):
				for i in range(3):
					if (deltaSclAnimated[i]):
						self.ExportAnimationTrack(deltaSclAnimCurve[i], deltaSclAnimKind[i], deltaSubscaleName[i], structFlag)
						structFlag = True

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

	# Replacement for 
	#   node.to_mesh(scene, applyModifiers, "RENDER", True, False)
	# TODO: handle other params
	def GetMesh( self, node, scene, applyModifiers ):

		if applyModifiers:
			depsgraph = self.ctx.evaluated_depsgraph_get()
			node = node.evaluated_get( depsgraph )

		return node.to_mesh( )

	def ExportBoneTransform(self, armature, bone, scene):

		curveArray = self.CollectBoneAnimation(armature, bone.name)
		animation = ((len(curveArray) != 0) or (self.sampleAnimationFlag))

		transform = bone.matrix_local.copy()
		parentBone = bone.parent
		if ((parentBone) and (math.fabs(parentBone.matrix_local.determinant()) > kExportEpsilon)):
			transform = parentBone.matrix_local.inverted() * transform

		poseBone = armature.pose.bones.get(bone.name)
		if (poseBone):
			transform = poseBone.matrix.copy()
			parentPoseBone = poseBone.parent
			if ((parentPoseBone) and (math.fabs(parentPoseBone.matrix.determinant()) > kExportEpsilon)):
				transform = parentPoseBone.matrix.inverted() * transform

		self.IndentWrite(B"Transform")

		if (animation):
			self.Write(B" %transform")

		self.IndentWrite(B"{\n", 0, True)
		self.indentLevel += 1

		self.IndentWrite(B"float[16]\n")
		self.IndentWrite(B"{\n")
		self.WriteMatrix(transform)
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		if ((animation) and (poseBone)):
			self.ExportBoneSampledAnimation(poseBone, scene)


	def ExportMaterialRef(self, material, index):
		if (not material in self.materialArray):
			self.materialArray[material] = {"structName" : bytes("material" + str(len(self.materialArray) + 1), "UTF-8")}

		self.IndentWrite(B"MaterialRef (index = ")
		self.WriteInt(index)
		self.Write(B") {ref {$")
		self.Write(self.materialArray[material]["structName"])
		self.Write(B"}}\n")


	def ExportMorphWeights(self, node, shapeKeys, scene):
		action = None
		curveArray = []
		indexArray = []

		if (shapeKeys.animation_data):
			action = shapeKeys.animation_data.action
			if (action):
				for fcurve in action.fcurves:
					if ((fcurve.data_path.startswith("key_blocks[")) and (fcurve.data_path.endswith("].value"))):
						keyName = fcurve.data_path.strip("abcdehklopstuvy[]_.")
						if ((keyName[0] == "\"") or (keyName[0] == "'")):
							index = shapeKeys.key_blocks.find(keyName.strip("\"'"))
							if (index >= 0):
								curveArray.append(fcurve)
								indexArray.append(index)
						else:
							curveArray.append(fcurve)
							indexArray.append(int(keyName))

		if ((not action) and (node.animation_data)):
			action = node.animation_data.action
			if (action):
				for fcurve in action.fcurves:
					if ((fcurve.data_path.startswith("data.shape_keys.key_blocks[")) and (fcurve.data_path.endswith("].value"))):
						keyName = fcurve.data_path.strip("abcdehklopstuvy[]_.")
						if ((keyName[0] == "\"") or (keyName[0] == "'")):
							index = shapeKeys.key_blocks.find(keyName.strip("\"'"))
							if (index >= 0):
								curveArray.append(fcurve)
								indexArray.append(index)
						else:
							curveArray.append(fcurve)
							indexArray.append(int(keyName))

		animated = (len(curveArray) != 0)
		referenceName = shapeKeys.reference_key.name if (shapeKeys.use_relative) else ""

		for k in range(len(shapeKeys.key_blocks)):
			self.IndentWrite(B"MorphWeight", 0, (k == 0))

			if (animated):
				self.Write(B" %mw")
				self.WriteInt(k)

			self.Write(B" (index = ")
			self.WriteInt(k)
			self.Write(B") {float {")

			block = shapeKeys.key_blocks[k]
			self.WriteFloat(block.value if (block.name != referenceName) else 1.0)

			self.Write(B"}}\n")

		if (animated):
			self.IndentWrite(B"Animation (begin = ", 0, True)
			self.WriteFloat((action.frame_range[0] - self.beginFrame) * self.frameTime)
			self.Write(B", end = ")
			self.WriteFloat((action.frame_range[1] - self.beginFrame) * self.frameTime)
			self.Write(B")\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			structFlag = False

			for a in range(len(curveArray)):
				k = indexArray[a]
				target = bytes("mw" + str(k), "UTF-8")

				fcurve = curveArray[a]
				kind = OpenGexExporter.ClassifyAnimationCurve(fcurve)
				if ((kind != kAnimationSampled) and (not self.sampleAnimationFlag)):
					self.ExportAnimationTrack(fcurve, kind, target, structFlag)
				else:
					self.ExportMorphWeightSampledAnimationTrack(shapeKeys.key_blocks[k], target, scene, structFlag)

				structFlag = True

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")


	def ExportBone(self, armature, bone, scene):
		nodeRef = self.nodeArray.get(bone)
		if (nodeRef):
			self.IndentWrite(structIdentifier[nodeRef["nodeType"]], 0, True)
			self.Write(nodeRef["structName"])

			self.IndentWrite(B"{\n", 0, True)
			self.indentLevel += 1

			name = bone.name
			if (name != ""):
				self.IndentWrite(B"Name {string {\"")
				self.Write(bytes(name, "UTF-8"))
				self.Write(B"\"}}\n\n")

			self.ExportBoneTransform(armature, bone, scene)

		for subnode in bone.children:
			self.ExportBone(armature, subnode, scene)

		# Export any ordinary nodes that are parented to this bone.

		boneSubnodeArray = self.boneParentArray.get(bone.name)
		if (boneSubnodeArray):
			poseBone = None
			if (not bone.use_relative_parent):
				poseBone = armature.pose.bones.get(bone.name)

			for subnode in boneSubnodeArray:
				self.ExportNode(subnode, scene, poseBone)

		if (nodeRef):
			self.indentLevel -= 1
			self.IndentWrite(B"}\n")


	def ExportNode(self, node, scene, poseBone = None):

		# This function exports a single node in the scene and includes its name,
		# object reference, material references (for geometries), and transform.
		# Subnodes are then exported recursively.

		nodeRef = self.nodeArray.get(node)
		if (nodeRef):
			type = nodeRef["nodeType"]
			self.IndentWrite(structIdentifier[type], 0, True)
			self.Write(nodeRef["structName"])

			if (type == kNodeTypeGeometry):
				if (node.hide_render):
					self.Write(B" (visible = false)")

			self.IndentWrite(B"{\n", 0, True)
			self.indentLevel += 1

			structFlag = False

			# Export the node's name if it has one.

			name = node.name
			if (name != ""):
				self.IndentWrite(B"Name {string {\"")
				self.Write(bytes(name, "UTF-8"))
				self.Write(B"\"}}\n")
				structFlag = True

			# Export the object reference and material references.

			object = node.data

			if (type == kNodeTypeGeometry):
				if (not object in self.geometryArray):

					# Attempt to sanitize name
					# @Note Disabled, we want to keep the same names as they are originally
					# in case we reimport the file.
					#geomName = object.name.replace(' ', '_')
					#geomName = geomName.replace('.', '_').lower()
					geomName = object.name


					self.geometryArray[object] = {"structName" : bytes(geomName, "UTF-8"), "nodeTable" : [node]}
				else:
					self.geometryArray[object]["nodeTable"].append(node)

				self.IndentWrite(B"ObjectRef {ref {$")
				self.Write(self.geometryArray[object]["structName"])
				self.Write(B"}}\n")

				if(self.option_export_materials):
					for i in range(len(node.material_slots)):
						self.ExportMaterialRef(node.material_slots[i].material, i)

				shapeKeys = OpenGexExporter.GetShapeKeys(object)
				if (shapeKeys):
					self.ExportMorphWeights(node, shapeKeys, scene)

				structFlag = True

			elif (type == kNodeTypeLight):
				if (not object in self.lightArray):
					self.lightArray[object] = {"structName" : bytes(object.name, "UTF-8"), "nodeTable" : [node]}
				else:
					self.lightArray[object]["nodeTable"].append(node)

				self.IndentWrite(B"ObjectRef {ref {$")
				self.Write(self.lightArray[object]["structName"])
				self.Write(B"}}\n")
				structFlag = True

			elif (type == kNodeTypeCamera):
				if (not object in self.cameraArray):
					self.cameraArray[object] = {"structName" : bytes(object.name, "UTF-8"), "nodeTable" : [node]}
				else:
					self.cameraArray[object]["nodeTable"].append(node)

				self.IndentWrite(B"ObjectRef {ref {$")
				self.Write(self.cameraArray[object]["structName"])
				self.Write(B"}}\n")
				structFlag = True

			if (structFlag):
				self.Write(B"\n")

			if (poseBone):

				# If the node is parented to a bone and is not relative, then undo the bone's transform.

				if (math.fabs(poseBone.matrix.determinant()) > kExportEpsilon):
					self.IndentWrite(B"Transform\n")
					self.IndentWrite(B"{\n")
					self.indentLevel += 1

					self.IndentWrite(B"float[16]\n")
					self.IndentWrite(B"{\n")
					self.WriteMatrix(poseBone.matrix.inverted())
					self.IndentWrite(B"}\n")

					self.indentLevel -= 1
					self.IndentWrite(B"}\n\n")

			# Export the transform. If the node is animated, then animation tracks are exported here.

			self.ExportNodeTransform(node, scene)

			if (node.type == "ARMATURE"):
				skeleton = node.data
				if (skeleton):
					for bone in skeleton.bones:
						if (not bone.parent):
							self.ExportBone(node, bone, scene)

		for subnode in node.children:
			if (subnode.parent_type != "BONE"):
				self.ExportNode(subnode, scene)

		if (nodeRef):
			self.indentLevel -= 1
			self.IndentWrite(B"}\n")


	def ExportSkin(self, node, armature, exportVertexArray):

		# This function exports all skinning data, which includes the skeleton
		# and per-vertex bone influence data.

		self.IndentWrite(B"Skin\n", 0, True)
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		# Write the skin bind pose transform.

		self.IndentWrite(B"Transform\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"float[16]\n")
		self.IndentWrite(B"{\n")
		self.WriteMatrix(node.matrix_world)
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Export the skeleton, which includes an array of bone node references
		# and and array of per-bone bind pose transforms.

		self.IndentWrite(B"Skeleton\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		# Write the bone node reference array.

		self.IndentWrite(B"BoneRefArray\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		boneArray = armature.data.bones
		boneCount = len(boneArray)

		self.IndentWrite(B"ref\t\t\t// ")
		self.WriteInt(boneCount)
		self.IndentWrite(B"{\n", 0, True)
		self.IndentWrite(B"", 1)

		for i in range(boneCount):
			boneRef = self.FindNode(boneArray[i].name)
			if (boneRef):
				self.Write(B"$")
				self.Write(boneRef[1]["structName"])
			else:
				self.Write(B"null")

			if (i < boneCount - 1):
				self.Write(B", ")
			else:
				self.Write(B"\n")

		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Write the bind pose transform array.

		self.IndentWrite(B"Transform\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"float[16]\t// ")
		self.WriteInt(boneCount)
		self.IndentWrite(B"{\n", 0, True)

		for i in range(boneCount):
			self.WriteMatrixFlat(armature.matrix_world * boneArray[i].matrix_local)
			if (i < boneCount - 1):
				self.Write(B",\n")

		self.IndentWrite(B"}\n", 0, True)

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Export the per-vertex bone influence data.

		groupRemap = []

		for group in node.vertex_groups:
			groupName = group.name
			for i in range(boneCount):
				if (boneArray[i].name == groupName):
					groupRemap.append(i)
					break
			else:
				groupRemap.append(-1)

		boneCountArray = []
		boneIndexArray = []
		boneWeightArray = []

		meshVertexArray = node.data.vertices
		for ev in exportVertexArray:
			boneCount = 0
			totalWeight = 0.0
			for element in meshVertexArray[ev.vertexIndex].groups:
				boneIndex = groupRemap[element.group]
				boneWeight = element.weight
				if ((boneIndex >= 0) and (boneWeight != 0.0)):
					boneCount += 1
					totalWeight += boneWeight
					boneIndexArray.append(boneIndex)
					boneWeightArray.append(boneWeight)
			boneCountArray.append(boneCount)

			if (totalWeight != 0.0):
				normalizer = 1.0 / totalWeight
				for i in range(-boneCount, 0):
					boneWeightArray[i] *= normalizer

		# Write the bone count array. There is one entry per vertex.

		self.IndentWrite(B"BoneCountArray\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"unsigned_int16\t\t// ")
		self.WriteInt(len(boneCountArray))
		self.IndentWrite(B"{\n", 0, True)
		self.WriteIntArray(boneCountArray)
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Write the bone index array. The number of entries is the sum of the bone counts for all vertices.

		self.IndentWrite(B"BoneIndexArray\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"unsigned_int16\t\t// ")
		self.WriteInt(len(boneIndexArray))
		self.IndentWrite(B"{\n", 0, True)
		self.WriteIntArray(boneIndexArray)
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Write the bone weight array. The number of entries is the sum of the bone counts for all vertices.

		self.IndentWrite(B"BoneWeightArray\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"float\t\t// ")
		self.WriteInt(len(boneWeightArray))
		self.IndentWrite(B"{\n", 0, True)
		self.WriteFloatArray(boneWeightArray)
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")


	def ExportGeometry(self, objectRef, scene):

		# This function exports a single geometry object.

		self.Write(B"\nGeometryObject $")
		self.Write(objectRef[1]["structName"])
		self.WriteNodeTable(objectRef)

		self.Write(B"\n{\n")
		self.indentLevel += 1

		node = objectRef[1]["nodeTable"][0]
		mesh = objectRef[0]

		structFlag = False;

		# Save the morph state if necessary.

		activeShapeKeyIndex = node.active_shape_key_index
		showOnlyShapeKey = node.show_only_shape_key
		currentMorphValue = []

		shapeKeys = OpenGexExporter.GetShapeKeys(mesh)
		if (shapeKeys):
			node.active_shape_key_index = 0
			node.show_only_shape_key = True

			baseIndex = 0
			relative = shapeKeys.use_relative
			if (relative):
				morphCount = 0
				baseName = shapeKeys.reference_key.name
				for block in shapeKeys.key_blocks:
					if (block.name == baseName):
						baseIndex = morphCount
						break
					morphCount += 1

			morphCount = 0
			for block in shapeKeys.key_blocks:
				currentMorphValue.append(block.value)
				block.value = 0.0

				if (block.name != ""):
					self.IndentWrite(B"Morph (index = ", 0, structFlag)
					self.WriteInt(morphCount)

					if ((relative) and (morphCount != baseIndex)):
						self.Write(B", base = ")
						self.WriteInt(baseIndex)

					self.Write(B")\n")
					self.IndentWrite(B"{\n")
					self.IndentWrite(B"Name {string {\"", 1)
					self.Write(bytes(block.name, "UTF-8"))
					self.Write(B"\"}}\n")
					self.IndentWrite(B"}\n")
					structFlag = True

				morphCount += 1

			shapeKeys.key_blocks[0].value = 1.0
			mesh.update()

		self.IndentWrite(B"Mesh (primitive = \"triangles\")\n", 0, structFlag)
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		armature = node.find_armature()
		applyModifiers = (not armature)

		# Apply all modifiers to create a new mesh with tessfaces.

		# We don't apply modifiers for a skinned mesh because we need the vertex positions
		# before they are deformed by the armature modifier in order to export the proper
		# bind pose. This does mean that modifiers preceding the armature modifier are ignored,
		# but the Blender API does not provide a reasonable way to retrieve the mesh at an
		# arbitrary stage in the modifier stack.

		exportMesh = self.GetMesh( node, scene, applyModifiers )

		# Triangulate mesh and remap vertices to eliminate duplicates.

		materialTable = []
		exportVertexArray = OpenGexExporter.DeindexMesh(exportMesh, materialTable, self.option_export_vertex_colors)
		triangleCount = len(materialTable)

		indexTable = []
		unifiedVertexArray = OpenGexExporter.UnifyVertices(exportVertexArray, indexTable)
		vertexCount = len(unifiedVertexArray)

		# Write the position array.

		self.IndentWrite(B"VertexArray (attrib = \"position\")\n")
		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"float[3]\t\t// ")
		self.WriteInt(vertexCount)
		self.IndentWrite(B"{\n", 0, True)
		self.WriteVertexArray3D(unifiedVertexArray, "position")
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.IndentWrite(B"}\n\n")

		# Write the normal array.
		if(self.option_export_normals):
			self.IndentWrite(B"VertexArray (attrib = \"normal\")\n")
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"float[3]\t\t// ")
			self.WriteInt(vertexCount)
			self.IndentWrite(B"{\n", 0, True)
			self.WriteVertexArray3D(unifiedVertexArray, "normal")
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		# Write the color array if it exists.
		colorCount = len(exportMesh.vertex_colors)
		if (colorCount > 0 and self.option_export_vertex_colors):
			self.IndentWrite(B"VertexArray (attrib = \"color\")\n", 0, True)
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"float[3]\t\t// ")
			self.WriteInt(vertexCount)
			self.IndentWrite(B"{\n", 0, True)
			self.WriteVertexArray3D(unifiedVertexArray, "color")
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		# Write the texcoord arrays.
		if(self.option_export_uvs):
			for uv_layer_index in range( len(mesh.uv_layers) ):

				if (uv_layer_index > 1):
					break

				if uv_layer_index > 0:
					attribSuffix = bytes( f"[{uv_layer_index}]", "UTF-8" )
				else:
					attribSuffix = B""

				self.IndentWrite(B"VertexArray (attrib = \"texcoord" + attribSuffix + B"\")\n", 0, True)
				self.IndentWrite(B"{\n")
				self.indentLevel += 1

				self.IndentWrite(B"float[2]\t\t// ")
				self.WriteInt(vertexCount )
				self.IndentWrite(B"{\n", 0, True)
				self.WriteVertexArray2D( unifiedVertexArray, "texcoord" + str(uv_layer_index) )
				self.IndentWrite(B"}\n")

				self.indentLevel -= 1
				self.IndentWrite(B"}\n")

		# Write morph targets.
		if (shapeKeys):
			shapeKeys.key_blocks[0].value = 0.0
			for m in range(1, len(currentMorphValue)):
				shapeKeys.key_blocks[m].value = 1.0
				mesh.update()

				node.active_shape_key_index = m
				#morphMesh = node.to_mesh(scene, applyModifiers, "RENDER", True, False)
				morphMesh = self.GetMesh( node, scene, applyModifiers )
				morphMesh.calc_loop_triangles()

				# Write the morph target position array.

				self.IndentWrite(B"VertexArray (attrib = \"position\", morph = ", 0, True)
				self.WriteInt(m)
				self.Write(B")\n")
				self.IndentWrite(B"{\n")
				self.indentLevel += 1

				self.IndentWrite(B"float[3]\t\t// ")
				self.WriteInt(vertexCount)
				self.IndentWrite(B"{\n", 0, True)
				self.WriteMorphPositionArray3D(unifiedVertexArray, morphMesh.vertices)
				self.IndentWrite(B"}\n")

				self.indentLevel -= 1
				self.IndentWrite(B"}\n\n")

				# Write the morph target normal array.

				self.IndentWrite(B"VertexArray (attrib = \"normal\", morph = ")
				self.WriteInt(m)
				self.Write(B")\n")
				self.IndentWrite(B"{\n")
				self.indentLevel += 1

				self.IndentWrite(B"float[3]\t\t// ")
				self.WriteInt(vertexCount)
				self.IndentWrite(B"{\n", 0, True)
				self.WriteMorphNormalArray3D(unifiedVertexArray, morphMesh.vertices, morphMesh.loop_triangles)
				self.IndentWrite(B"}\n")

				self.indentLevel -= 1
				self.IndentWrite(B"}\n")

				# Delete morphMesh
				node.to_mesh_clear()

		# Write the index arrays.

		maxMaterialIndex = 0
		for i in range(len(materialTable)):
			index = materialTable[i]
			if (index > maxMaterialIndex):
				maxMaterialIndex = index

		if (maxMaterialIndex == 0):
			
			# There is only one material, so write a single index array.

			self.IndentWrite(B"IndexArray\n", 0, True)
			self.IndentWrite(B"{\n")
			self.indentLevel += 1

			self.IndentWrite(B"unsigned_int32[3]\t\t// ")
			self.WriteInt(triangleCount)
			self.IndentWrite(B"{\n", 0, True)
			self.WriteTriangleArray(triangleCount, indexTable)
			self.IndentWrite(B"}\n")

			self.indentLevel -= 1
			self.IndentWrite(B"}\n")

		else:

			# If there are multiple material indexes, then write a separate index array for each one.

			materialTriangleCount = [0 for i in range(maxMaterialIndex + 1)]
			for i in range(len(materialTable)):
				materialTriangleCount[materialTable[i]] += 1

			for m in range(maxMaterialIndex + 1):
				if (materialTriangleCount[m] != 0):
					materialIndexTable = []
					for i in range(len(materialTable)):
						if (materialTable[i] == m):
							k = i * 3
							materialIndexTable.append(indexTable[k])
							materialIndexTable.append(indexTable[k + 1])
							materialIndexTable.append(indexTable[k + 2])

					self.IndentWrite(B"IndexArray (material = ", 0, True)
					self.WriteInt(m)
					self.Write(B")\n")
					self.IndentWrite(B"{\n")
					self.indentLevel += 1

					self.IndentWrite(B"unsigned_int32[3]\t\t// ")
					self.WriteInt(materialTriangleCount[m])
					self.IndentWrite(B"{\n", 0, True)
					self.WriteTriangleArray(materialTriangleCount[m], materialIndexTable)
					self.IndentWrite(B"}\n")

					self.indentLevel -= 1
					self.IndentWrite(B"}\n")

		# If the mesh is skinned, export the skinning data here.

		if (armature):
			self.ExportSkin(node, armature, unifiedVertexArray)

		# Restore the morph state.

		if (shapeKeys):
			node.active_shape_key_index = activeShapeKeyIndex
			node.show_only_shape_key = showOnlyShapeKey

			for m in range(len(currentMorphValue)):
				shapeKeys.key_blocks[m].value = currentMorphValue[m]

			mesh.update()

		# Delete the new mesh that we made earlier.
		node.to_mesh_clear()

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

		self.indentLevel -= 1
		self.Write(B"}\n")


	def ExportLight(self, objectRef):

		# This function exports a single light object.

		self.Write(B"\nLightObject $")
		self.Write(objectRef[1]["structName"])

		object = objectRef[0]
		type = object.type

		self.Write(B" (type = ")
		pointFlag = False
		spotFlag = False

		if (type == "SUN"):
			self.Write(B"\"infinite\"")
		elif (type == "POINT"):
			self.Write(B"\"point\"")
			pointFlag = True
		else:
			self.Write(B"\"spot\"")
			pointFlag = True
			spotFlag = True

		if (not object.use_shadow):
			self.Write(B", shadow = false")

		self.Write(B")")
		self.WriteNodeTable(objectRef)

		self.Write(B"\n{\n")
		self.indentLevel += 1

		# Export the light's color, and include a separate intensity if necessary.

		self.IndentWrite(B"Color (attrib = \"light\") {float[3] {")
		self.WriteColor(object.color)
		self.Write(B"}}\n")

		intensity = object.energy
		if (intensity != 1.0):
			self.IndentWrite(B"Param (attrib = \"intensity\") {float {")
			self.WriteFloat(intensity)
			self.Write(B"}}\n")


		if (pointFlag):

			radius = object.shadow_soft_size # Odd naming for light radius.
			if (radius > 0):
				self.IndentWrite(B"Param (attrib = \"radius\") {float {")
				self.WriteFloat(radius)
				self.Write(B"}}\n")

			# Export a separate attenuation function for each type that's in use.

			falloff = object.falloff_type

			if (falloff == "INVERSE_LINEAR"):
				self.IndentWrite(B"Atten (curve = \"inverse\")\n", 0, True)
				self.IndentWrite(B"{\n")

				self.IndentWrite(B"Param (attrib = \"scale\") {float {", 1)
				self.WriteFloat(object.distance)
				self.Write(B"}}\n")

				self.IndentWrite(B"}\n")

			elif (falloff == "INVERSE_SQUARE"):
				self.IndentWrite(B"Atten (curve = \"inverse_square\")\n", 0, True)
				self.IndentWrite(B"{\n")

				self.IndentWrite(B"Param (attrib = \"scale\") {float {", 1)
				self.WriteFloat(math.sqrt(object.distance))
				self.Write(B"}}\n")

				self.IndentWrite(B"}\n")

			elif (falloff == "LINEAR_QUADRATIC_WEIGHTED"):
				if (object.linear_attenuation != 0.0):
					self.IndentWrite(B"Atten (curve = \"inverse\")\n", 0, True)
					self.IndentWrite(B"{\n")

					self.IndentWrite(B"Param (attrib = \"scale\") {float {", 1)
					self.WriteFloat(object.distance)
					self.Write(B"}}\n")

					self.IndentWrite(B"Param (attrib = \"constant\") {float {", 1)
					self.WriteFloat(1.0)
					self.Write(B"}}\n")

					self.IndentWrite(B"Param (attrib = \"linear\") {float {", 1)
					self.WriteFloat(object.linear_attenuation)
					self.Write(B"}}\n")

					self.IndentWrite(B"}\n\n")

				if (object.quadratic_attenuation != 0.0):
					self.IndentWrite(B"Atten (curve = \"inverse_square\")\n")
					self.IndentWrite(B"{\n")

					self.IndentWrite(B"Param (attrib = \"scale\") {float {", 1)
					self.WriteFloat(object.distance)
					self.Write(B"}}\n")

					self.IndentWrite(B"Param (attrib = \"constant\") {float {", 1)
					self.WriteFloat(1.0)
					self.Write(B"}}\n")

					self.IndentWrite(B"Param (attrib = \"quadratic\") {float {", 1)
					self.WriteFloat(object.quadratic_attenuation)
					self.Write(B"}}\n")

					self.IndentWrite(B"}\n")

			if (spotFlag):

				# Export additional angular attenuation for spot lights.

				self.IndentWrite(B"Atten (kind = \"angle\", curve = \"linear\")\n", 0, True)
				self.IndentWrite(B"{\n")

				endAngle = object.spot_size * 0.5
				beginAngle = endAngle * (1.0 - object.spot_blend)

				self.IndentWrite(B"Param (attrib = \"begin\") {float {", 1)
				self.WriteFloat(beginAngle)
				self.Write(B"}}\n")

				self.IndentWrite(B"Param (attrib = \"end\") {float {", 1)
				self.WriteFloat(endAngle)
				self.Write(B"}}\n")

				self.IndentWrite(B"}\n")
		
		else: # Directional/Infinite/Sun
			self.IndentWrite(B"Param (attrib = \"angle\") {float {")
			self.WriteFloat(object.angle)
			self.Write(B"}}\n")

		self.indentLevel -= 1
		self.Write(B"}\n")


	def ExportCamera(self, objectRef):

		# This function exports a single camera object.

		self.Write(B"\nCameraObject $")
		self.Write(objectRef[1]["structName"])
		self.WriteNodeTable(objectRef)

		self.Write(B"\n{\n")
		self.indentLevel += 1

		object = objectRef[0]

		self.IndentWrite(B"Param (attrib = \"fovy\") {float {")
		self.WriteFloat(object.angle_y)
		self.Write(B"}}\n")

		self.IndentWrite(B"Param (attrib = \"near\") {float {")
		self.WriteFloat(object.clip_start)
		self.Write(B"}}\n")

		self.IndentWrite(B"Param (attrib = \"far\") {float {")
		self.WriteFloat(object.clip_end)
		self.Write(B"}}\n")

		self.indentLevel -= 1
		self.Write(B"}\n")


	def ExportObjects(self, scene):
		for objectRef in self.geometryArray.items():
			self.ExportGeometry(objectRef, scene)
		for objectRef in self.lightArray.items():
			self.ExportLight(objectRef)
		for objectRef in self.cameraArray.items():
			self.ExportCamera(objectRef)

	def FindTextureInNodeTree(self, bsdf, channel):

		curr = bsdf.inputs[channel]

		while curr and curr.is_linked:
			node = curr.links[0].from_socket.node

			if (node.type == 'TEX_IMAGE'):
				return node.image

			# Wasn't an image name, walk back links for now..
			curr = None
			backLinks = ["Color"]
			for backlinkName in backLinks:
				curr = node.inputs.get(backlinkName, None)
				break

		return None

	def FindNormalMapInNodeTree(self, bsdf, channel):

		curr = bsdf.inputs[channel]

		while curr and curr.is_linked:
			node = curr.links[0].from_socket.node

			if (node.type == 'TEX_IMAGE'):
				return node.image

			# Wasn't an image name, walk back links for now..
			curr = None
			backLinks = ["Color", "Normal"]
			for backlinkName in backLinks:
				curr = node.inputs.get(backlinkName, None)
				break

		return None


	def ExportImageNodeTexture(self, image, attrib ):

		# This function exports a single texture from a material.

		self.IndentWrite(B"Texture (attrib = \"", 0, False )
		self.Write(attrib)
		self.Write(B"\")\n")

		self.IndentWrite(B"{\n")
		self.indentLevel += 1

		self.IndentWrite(B"string {\"")
		self.WriteFileName(os.path.basename(image.filepath))
		self.Write(B"\"}\n")

		# TODO: look for a vector transform node and convert the scale/offsets

		self.indentLevel -= 1
		self.IndentWrite(B"}\n")

	def ExportMaterialParam(self, bsdf, blenderParamName, ogexParamName, propertyFlags, defaultValue = 0.0 ):

		channel = bsdf.inputs[blenderParamName]
		if not channel:
			return

		didWriteValue = False

		# Color and Param are exclusive, only should be present
		if MaterialPropertyFlags.PropertyColor in propertyFlags:

			if type(channel) == bpy.types.NodeSocketColor:
				color = tuple( channel.default_value )
			elif type(channel) == bpy.types.NodeSocketFloatFactor:
				value = channel.default_value
				color = ( value, value, value )

			if ((color[0] != defaultValue) and (color[1] != defaultValue ) and (color[2] != defaultValue )):
				didWriteValue = True
				self.IndentWrite(B"Color (attrib = \"" + ogexParamName + B"\") {float[3] {")
				self.WriteColor(color)
				self.Write(B"}}\n")

		elif MaterialPropertyFlags.PropertyParam in propertyFlags:

			if type(channel) == bpy.types.NodeSocketColor:
				value = channel.default_value[0]
			elif type(channel) == bpy.types.NodeSocketFloatFactor:
				value = channel.default_value

			if (value != defaultValue):
				didWriteValue = True
				self.IndentWrite(B"Param (attrib = \"" + ogexParamName + B"\") {float {")
				self.WriteFloat(value)
				self.Write(B"}}\n")

		if MaterialPropertyFlags.PropertyTexture in propertyFlags:
			textureNode = self.FindTextureInNodeTree(bsdf, blenderParamName)
			if textureNode:
				self.ExportImageNodeTexture( textureNode, ogexParamName )
				didWriteValue = True

		if (didWriteValue):
			self.Write(B"\n")

	def ExportNormalMap( self, bsdf ):

		normalMap = self.FindNormalMapInNodeTree(bsdf, "Normal")
		if normalMap:
			self.ExportImageNodeTexture(normalMap, B"normal")
			self.Write(B"\n")


	def ExportMaterials(self):

		# This function exports all of the materials used in the scene.
		if(not self.option_export_materials):
			return

		for materialRef in self.materialArray.items():
			material = materialRef[0]

			self.Write(B"\nMaterial $")
			self.Write(materialRef[1]["structName"])
			self.Write(B"\n{\n")
			self.indentLevel += 1

			if (material.name != ""):
				self.IndentWrite(B"Name {string {\"")
				self.Write(bytes(material.name, "UTF-8"))
				self.Write(B"\"}}\n\n")

			bsdf = None
			if material.node_tree:
				nodes = material.node_tree.nodes

				# This exporter requires you are using Principled BSDF. Might want to add a case to support Mix Shader
				# with an emission or transparency shader since that is a common setup.
				bsdf = nodes.get('Principled BSDF', None )

			if bsdf:
				# Shortcuts for common types of flags
				flagsColorOrTexture = ( MaterialPropertyFlags.PropertyColor, MaterialPropertyFlags.PropertyTexture )
				flagsParamOrTexture = (MaterialPropertyFlags.PropertyParam, MaterialPropertyFlags.PropertyTexture)

				# See chart on Table 2.1 of OGEX spec for details of how these map
				self.ExportMaterialParam(bsdf, "Base Color", b"diffuse", flagsColorOrTexture )
				self.ExportMaterialParam(bsdf, "Specular", b"specular", flagsColorOrTexture)
				self.ExportMaterialParam(bsdf, "Roughness", b"roughness", flagsParamOrTexture)
				self.ExportMaterialParam(bsdf, "Metallic", b"metalness", flagsParamOrTexture)
				self.ExportMaterialParam(bsdf, "Emission", b"emission", flagsColorOrTexture )
				self.ExportMaterialParam(bsdf, "Alpha", b"opacity", flagsParamOrTexture, 1.0 )
				self.ExportNormalMap( bsdf )

			self.indentLevel -= 1
			self.Write(B"}\n")


	def ExportMetrics(self, scene):
		scale = scene.unit_settings.scale_length

		if (scene.unit_settings.system == "IMPERIAL"):
			scale *= 0.3048

		self.Write(B"Metric (key = \"distance\") {float {")
		self.WriteFloat(scale)
		self.Write(B"}}\n")

		self.Write(B"Metric (key = \"angle\") {float {1.0}}\n")
		self.Write(B"Metric (key = \"time\") {float {1.0}}\n")
		self.Write(B"Metric (key = \"up\") {string {\"z\"}}\n")


	def execute(self, context):
		print('\nOpenGex export starting... %r' % self.filepath)
		start_time = time.process_time()

		self.file = open(self.filepath, "wb")

		self.indentLevel = 0
		self.ctx = context

		scene = context.scene
		self.ExportMetrics(scene)

		originalFrame = scene.frame_current
		originalSubframe = scene.frame_subframe
		self.restoreFrame = False

		self.beginFrame = scene.frame_start
		self.endFrame = scene.frame_end
		self.frameTime = 1.0 / (scene.render.fps_base * scene.render.fps)

		self.nodeArray = {}
		self.geometryArray = {}
		self.lightArray = {}
		self.cameraArray = {}
		self.materialArray = {}
		self.boneParentArray = {}

		self.exportAllFlag = not self.option_export_selection
		self.sampleAnimationFlag = self.option_sample_animation

		for object in scene.objects:
			if (not object.parent):
				self.ProcessNode(object)

		self.ProcessSkinnedMeshes()

		for object in scene.objects:
			if (not object.parent):
				self.ExportNode(object, scene)

		self.ExportObjects(scene)
		self.ExportMaterials()

		if (self.restoreFrame):
			scene.frame_set(originalFrame, originalSubframe)

		self.file.close()

		print('Export finished in %.4f sec.' % (time.process_time() - start_time))
		return {'FINISHED'}



def menu_func(self, context):
	self.layout.operator(OpenGexExporter.bl_idname, text = "OpenGEX (.ogex)")

def register():
	bpy.utils.register_class(OpenGexExporter)
	bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
	bpy.types.TOPBAR_MT_file_export.remove(menu_func)
	bpy.utils.unregister_class(OpenGexExporter)

if __name__ == "__main__":
	register()