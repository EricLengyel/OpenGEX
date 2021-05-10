//
// OpenGEX exporter for Maya
// Version 3.0
//
// This file is part of the Open Game Engine Exchange library, by Eric Lengyel.
// Copyright 2013-2021, Terathon Software LLC
//
// This software is licensed under the GNU General Public License version 3.
// Separate proprietary licenses are available from Terathon Software.
//
// THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
// EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
// OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. 
//


#include "OpenGex-Maya.h"


namespace
{
	const float kDegToRad = 0.01745329252F;		// pi / 180
	const float kExportEpsilon = 1.0e-6F;		// Values smaller than this are considered to be zero.
}


using namespace OpenGex;


ExportVertex::ExportVertex()
{
	for (int i = 0; i < kMaxVertexColorCount; i++)
	{
		color[i].set(MColor::kRGB, 1.0F, 1.0F, 1.0F, 1.0F);
	}

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		texcoord[i][0] = 0.0F;
		texcoord[i][1] = 0.0F;
	}
}

bool ExportVertex::operator ==(const ExportVertex& v) const
{
	if (hash != v.hash)
	{
		return (false);
	}

	if (position != v.position)
	{
		return (false);
	}

	if (normal != v.normal)
	{
		return (false);
	}

	for (int i = 0; i < kMaxVertexColorCount; i++)
	{
		if (color[i] != v.color[i])
		{
			return (false);
		}
	}

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		if ((texcoord[i][0] != v.texcoord[i][0]) || (texcoord[i][1] != v.texcoord[i][1]))
		{
			return (false);
		}
	}

	return (true);
}

void ExportVertex::Hash(void)
{
	const unsigned int *data = reinterpret_cast<const unsigned int *>(&position.x);

	unsigned int h = data[0];
	h = ((h << 5) | (h >> 26)) + data[1];
	h = ((h << 5) | (h >> 26)) + data[2];

	data = reinterpret_cast<const unsigned int *>(&normal.x);

	h = ((h << 5) | (h >> 26)) + data[0];
	h = ((h << 5) | (h >> 26)) + data[1];
	h = ((h << 5) | (h >> 26)) + data[2];

	for (int i = 0; i < kMaxVertexColorCount; i++)
	{
		data = reinterpret_cast<const unsigned int *>(&color[i].r);

		h = ((h << 5) | (h >> 26)) + data[0];
		h = ((h << 5) | (h >> 26)) + data[1];
		h = ((h << 5) | (h >> 26)) + data[2];
		h = ((h << 5) | (h >> 26)) + data[3];
	}

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		data = reinterpret_cast<const unsigned int *>(texcoord[i]);

		h = ((h << 5) | (h >> 26)) + data[0];
		h = ((h << 5) | (h >> 26)) + data[1];
	}

	hash = h;
}


OpenGexExport::OpenGexExport()
{
}

OpenGexExport::~OpenGexExport()
{
}

void *OpenGexExport::New(void)
{
	return (new OpenGexExport);
}

MStatus OpenGexExport::writer(const MFileObject& file, const MString& optionsString, FileAccessMode mode)
{
	MDagPath		dagPath;
	MSelectionList	selectionList;

	exportFile = CreateFileW(file.resolvedFullName().asWChar(), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
	if (exportFile == INVALID_HANDLE_VALUE)
	{
		return (MS::kFailure);
	}

	indentLevel = 0;

	ExportMetrics();

	nodeArray = new std::vector<NodeReference>;
	geometryArray = new std::vector<ObjectReference>;
	lightArray = new std::vector<ObjectReference>;
	cameraArray = new std::vector<ObjectReference>;
	materialArray = new std::vector<MaterialReference>;
	textureArray = new std::vector<TextureReference>;

	const MSelectionList *exportList = nullptr;
	if (mode == kExportActiveAccessMode)
	{
		exportList = &selectionList;
		MGlobal::getActiveSelectionList(selectionList);
	}

	MItDag dagIterator(MItDag::kBreadthFirst);
	MObject rootNode = dagIterator.currentItem();

	dagIterator.getPath(dagPath);
	unsigned int nodeCount = dagPath.childCount();

	for (unsigned int i = 0; i < nodeCount; i++)
	{
		MDagPath childPath(dagPath);
		childPath.push(dagPath.child(i));
		ProcessNode(childPath, exportList);
	}

	ProcessSkinnedMeshes();

	for (unsigned int i = 0; i < nodeCount; i++)
	{
		MDagPath childPath(dagPath);
		childPath.push(dagPath.child(i));
		ExportNode(childPath, rootNode);
	}

	ExportObjects();
	ExportMaterials();

	delete textureArray;
	delete materialArray;
	delete cameraArray;
	delete lightArray;
	delete geometryArray;
	delete nodeArray;

	CloseHandle(exportFile);
	return (MS::kSuccess);
}

bool OpenGexExport::haveWriteMethod(void) const
{
	return (true);
}

MString OpenGexExport::defaultExtension(void) const
{
	return (MString("ogex"));
}

MPxFileTranslator::MFileKind OpenGexExport::identifyFile(const MFileObject& file, const char *buffer, short size) const
{
	MString name = file.rawName();
	unsigned int length = name.length();

	if ((length > 5) && (name.substring(length - 5, length - 1).toLowerCase() == ".ogex"))
	{
		return (MFileKind::kIsMyFileType);
	}

	return (MFileKind::kNotMyFileType);
}


void OpenGexExport::Write(const void *buffer, unsigned int size) const
{
	DWORD		actual;

	WriteFile(exportFile, buffer, size, &actual, nullptr);
}

void OpenGexExport::Write(const char *string) const
{
	const char *s = string;
	while (*s != 0)
	{
		s++;
	}

	if (s != string)
	{
		Write(string, (unsigned int) (s - string));
	}
}

void OpenGexExport::Write(const wchar_t *string) const
{
	// Convert a UTF-16 string to UTF-8, and write it to the file.

	const wchar_t *s = string;
	while (*s != 0)
	{
		s++;
	}

	if (s != string)
	{
		unsigned int length = (unsigned int) (s - string);
		char *buffer = new char[length * 4];

		int size = 0;
		for (unsigned int i = 0; i < length; i++)
		{
			unsigned int code = string[i] & 0xFFFF;

			if (code <= 0x007F)
			{
				if (code == 34)
				{
					buffer[size] = 92;
					buffer[size + 1] = 34;
					size += 2;
				}
				else if (code == 92)
				{
					buffer[size] = 92;
					buffer[size + 1] = 92;
					size += 2;
				}
				else
				{
					buffer[size] = (char) code;
					size += 1;
				}
			}
			else if (code <= 0x07FF)
			{
				buffer[size] = (char) (((code >> 6) & 0x1F) | 0xC0);
				buffer[size + 1] = (char) ((code & 0x3F) | 0x80);
				size += 2;
			}
			else
			{
				unsigned int p1 = code - 0xD800;
				if (p1 < 0x0400U)
				{
					unsigned int p2 = (string[i + 1] & 0xFFFF) - 0xDC00;
					if (p2 < 0x0400U)
					{
						code = ((p1 << 10) | p2) + 0x010000;
						i++;
					}
				}

				if (code <= 0x00FFFF)
				{
					buffer[size] = (char) (((code >> 12) & 0x0F) | 0xE0);
					buffer[size + 1] = (char) (((code >> 6) & 0x3F) | 0x80);
					buffer[size + 2] = (char) ((code & 0x3F) | 0x80);
					size += 3;
				}
				else
				{
					buffer[size] = (char) (((code >> 18) & 0x07) | 0xF0);
					buffer[size + 1] = (char) (((code >> 12) & 0x3F) | 0x80);
					buffer[size + 2] = (char) (((code >> 6) & 0x3F) | 0x80);
					buffer[size + 3] = (char) ((code & 0x3F) | 0x80);
					size += 4;
				}
			}
		}

		Write(buffer, size);
		delete[] buffer;
	}
}

void OpenGexExport::IndentWrite(const char *string, int extra, bool newline) const
{
	static const char tabs[16] = {9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9};

	if (newline)
	{
		Write("\n");
	}

	int indent = indentLevel + extra;

	int count = indent >> 4;
	for (int i = 0; i < count; i++)
	{
		Write(tabs, 16);
	}

	indent &= 15;
	if (indent != 0)
	{
		Write(tabs, indent);
	}

	Write(string);
}

void OpenGexExport::WriteInt(int i) const
{
	std::ostringstream	string;

	string << i;
	Write(string.str().c_str());
}

void OpenGexExport::WriteUnsignedInt(unsigned int i) const
{
	std::ostringstream	string;

	string << i;
	Write(string.str().c_str());
}

void OpenGexExport::WriteFloat(float f) const
{
	std::ostringstream	string;

	string << f;
	Write(string.str().c_str());
}

void OpenGexExport::WriteHexFloat(float f) const
{
	static const char hexdigit[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};

	static char string[11] = "0x00000000";

	unsigned int i = *(unsigned int *) &f;
	string[2] = hexdigit[(i >> 28) & 0x0F];
	string[3] = hexdigit[(i >> 24) & 0x0F];
	string[4] = hexdigit[(i >> 20) & 0x0F];
	string[5] = hexdigit[(i >> 16) & 0x0F];
	string[6] = hexdigit[(i >> 12) & 0x0F];
	string[7] = hexdigit[(i >> 8) & 0x0F];
	string[8] = hexdigit[(i >> 4) & 0x0F];
	string[9] = hexdigit[i & 0x0F];

	Write(string);
}

void OpenGexExport::WriteMatrix(const MMatrix& matrix) const
{
	const double *row = matrix[0];

	IndentWrite("{", 1);
	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000,\t\t// {");
	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0,\n");

	row = matrix[1];

	IndentWrite(" ", 1);
	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000,\t\t//  ");
	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0,\n");

	row = matrix[2];

	IndentWrite(" ", 1);
	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000,\t\t//  ");
	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0,\n");

	row = matrix[3];

	IndentWrite(" ", 1);
	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x3F800000}\t\t//  ");
	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 1}\n");
}

void OpenGexExport::WriteMatrixFlat(const MMatrix& matrix) const
{
	const double *row = matrix[0];

	IndentWrite("{", 1);
	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0, ");

	row = matrix[1];

	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0, ");

	row = matrix[2];

	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 0, ");

	row = matrix[3];

	WriteFloat(float(row[0]));
	Write(", ");
	WriteFloat(float(row[1]));
	Write(", ");
	WriteFloat(float(row[2]));
	Write(", 1}");
}

void OpenGexExport::WriteHexMatrixFlat(const MMatrix& matrix) const
{
	const double *row = matrix[0];

	IndentWrite("{", 1);
	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000, ");

	row = matrix[1];

	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000, ");

	row = matrix[2];

	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x00000000, ");

	row = matrix[3];

	WriteHexFloat(float(row[0]));
	Write(", ");
	WriteHexFloat(float(row[1]));
	Write(", ");
	WriteHexFloat(float(row[2]));
	Write(", 0x3F800000}");
}

void OpenGexExport::WriteVector(const MVector& vector) const
{
	Write("{");
	WriteFloat(float(vector.x));
	Write(", ");
	WriteFloat(float(vector.y));
	Write(", ");
	WriteFloat(float(vector.z));
	Write("}");
}

void OpenGexExport::WriteHexVector(const MVector& vector) const
{
	Write("{");
	WriteHexFloat(float(vector.x));
	Write(", ");
	WriteHexFloat(float(vector.y));
	Write(", ");
	WriteHexFloat(float(vector.z));
	Write("}");
}

void OpenGexExport::WriteQuaternion(const MQuaternion& quat) const
{
	Write("{");
	WriteFloat(float(quat.x));
	Write(", ");
	WriteFloat(float(quat.y));
	Write(", ");
	WriteFloat(float(quat.z));
	Write(", ");
	WriteFloat(float(quat.w));
	Write("}");
}

void OpenGexExport::WriteHexQuaternion(const MQuaternion& quat) const
{
	Write("{");
	WriteHexFloat(float(quat.x));
	Write(", ");
	WriteHexFloat(float(quat.y));
	Write(", ");
	WriteHexFloat(float(quat.z));
	Write(", ");
	WriteHexFloat(float(quat.w));
	Write("}");
}

void OpenGexExport::WriteColor(const MColor& color) const
{
	Write("{");
	WriteFloat(color.r);
	Write(", ");
	WriteFloat(color.g);
	Write(", ");
	WriteFloat(color.b);
	Write("}");
}

void OpenGexExport::WriteFileName(const char *string) const
{
	const char *s = string;
	while (*s != 0)
	{
		s++;
	}

	if (s != string)
	{
		unsigned int length = (unsigned int) (s - string);
		char *buffer = new char[length + 3];

		unsigned int i = 0;

		if ((length >= 2) && (string[1] == ':'))
		{
			buffer[0] = '/';
			buffer[1] = '/';
			buffer[2] = string[0];
			string += 2;
			i = 3;
		}

		for (;; string++)
		{
			char c = string[0];
			if (c == 0)
			{
				break;
			}

			if (c == '\\')
			{
				c = '/';
			}

			buffer[i] = c;
			i++;
		}

		buffer[i] = 0;
		Write(buffer);
		delete[] buffer;
	}
}

void OpenGexExport::WriteIntArray(int count, const int *value) const
{
	int lineCount = count >> 6;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 63; j++)
		{
			WriteInt(value[j]);
			Write(", ");
		}

		WriteInt(value[63]);
		value += 64;

		if (i * 64 < count - 64)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 63;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteInt(value[0]);
			Write(", ");
			value++;
		}

		WriteInt(value[0]);
		Write("\n");
	}
}

void OpenGexExport::WriteFloatArray(int count, const float *value) const
{
	int lineCount = count >> 4;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 15; j++)
		{
			WriteHexFloat(value[j]);
			Write(", ");
		}

		WriteHexFloat(value[15]);
		value += 16;

		if (i * 16 < count - 16)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 15;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteHexFloat(value[0]);
			Write(", ");
			value++;
		}

		WriteHexFloat(value[0]);
		Write("\n");
	}
}

void OpenGexExport::WriteVertex(const float (& vertex)[2]) const
{
	Write("{");
	WriteHexFloat(vertex[0]);
	Write(", ");
	WriteHexFloat(vertex[1]);
	Write("}");
}

void OpenGexExport::WriteVertex(const MFloatVector& vertex) const
{
	Write("{");
	WriteHexFloat(vertex.x);
	Write(", ");
	WriteHexFloat(vertex.y);
	Write(", ");
	WriteHexFloat(vertex.z);
	Write("}");
}

void OpenGexExport::WriteVertex(const MColor& vertex) const
{
	Write("{");
	WriteHexFloat(vertex.r);
	Write(", ");
	WriteHexFloat(vertex.g);
	Write(", ");
	WriteHexFloat(vertex.b);
	Write("}");
}

template <class type> void OpenGexExport::WriteVertexArray(int count, const type *vertex, int stride) const
{
	int lineCount = count >> 3;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 7; j++)
		{
			WriteVertex(vertex[0]);
			Write(", ");
			vertex = reinterpret_cast<const type *>(reinterpret_cast<const char *>(vertex) + stride);
		}

		WriteVertex(vertex[0]);
		vertex = reinterpret_cast<const type *>(reinterpret_cast<const char *>(vertex) + stride);

		if (i * 8 < count - 8)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 7;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteVertex(vertex[0]);
			Write(", ");
			vertex = reinterpret_cast<const type *>(reinterpret_cast<const char *>(vertex) + stride);
		}

		WriteVertex(vertex[0]);
		Write("\n");
	}
}

void OpenGexExport::WriteMorphVertexArray(int count, const ExportVertex *exportVertex, const MFloatPointArray& morphVertexArray)
{
	int lineCount = count >> 3;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 7; j++)
		{
			WriteVertex(morphVertexArray[exportVertex->vertexIndex]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphVertexArray[exportVertex->vertexIndex]);
		exportVertex++;

		if (i * 8 < count - 8)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 7;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteVertex(morphVertexArray[exportVertex->vertexIndex]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphVertexArray[exportVertex->vertexIndex]);
		Write("\n");
	}
}

void OpenGexExport::WriteMorphNormalArray(int count, const ExportVertex *exportVertex, const MFloatVectorArray& morphNormalArray)
{
	int lineCount = count >> 3;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 7; j++)
		{
			WriteVertex(morphNormalArray[exportVertex->normalIndex]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphNormalArray[exportVertex->normalIndex]);
		exportVertex++;

		if (i * 8 < count - 8)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 7;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteVertex(morphNormalArray[exportVertex->normalIndex]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphNormalArray[exportVertex->normalIndex]);
		Write("\n");
	}
}

void OpenGexExport::WriteTriangle(int triangleIndex, const int *indexTable) const
{
	int i = triangleIndex * 3;

	Write("{");
	WriteUnsignedInt(indexTable[i]);
	Write(", ");
	WriteUnsignedInt(indexTable[i + 1]);
	Write(", ");
	WriteUnsignedInt(indexTable[i + 2]);
	Write("}");
}

void OpenGexExport::WriteTriangleArray(int count, const int *indexTable) const
{
	int triangleIndex = 0;

	int lineCount = count >> 4;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 15; j++)
		{
			WriteTriangle(triangleIndex, indexTable);
			Write(", ");
			triangleIndex++;
		}

		WriteTriangle(triangleIndex, indexTable);
		triangleIndex++;

		if (i * 16 < count - 16)
		{
			Write(",\n");
		}
		else
		{
			Write("\n");
		}
	}

	count &= 15;
	if (count != 0)
	{
		IndentWrite("", 1);
		for (int j = count - 2; j >= 0; j--)
		{
			WriteTriangle(triangleIndex, indexTable);
			Write(", ");
			triangleIndex++;
		}

		WriteTriangle(triangleIndex, indexTable);
		Write("\n");
	}
}

void OpenGexExport::WriteNodeTable(const ObjectReference *objectRef) const
{
	bool first = true;
	int nodeCount = (int) objectRef->nodeTable.size();
	const MObject *nodeTable = &objectRef->nodeTable.front();
	for (int k = 0; k < nodeCount; k++)
	{
		MFnDagNode dagNode(nodeTable[k]);
		MString string = dagNode.name();

		const char *name = string.asUTF8();
		if ((name) && (name[0] != 0))
		{
			if (first)
			{
				Write("\t\t// ");
			}
			else
			{
				Write(", ");
			}

			Write(name);
			first = false;
		}
	}
}

int OpenGexExport::GetNodeType(const MObject& node, int *childIndex) const
{
	// This function classifies a node based on its own type and the type of any child that's a shape node.

	MFn::Type type = node.apiType();

	if (type == MFn::kJoint)
	{
		return (kNodeTypeNode);
	}

	if (type == MFn::kTransform)
	{
		MFnDagNode dagNode(node);

		bool transform = false;

		unsigned int subnodeCount = dagNode.childCount();
		for (unsigned int i = 0; i < subnodeCount; i++)
		{
			MObject subnode = dagNode.child(i);
			MFn::Type subtype = subnode.apiType();

			if ((subtype == MFn::kTransform) || (subtype == MFn::kJoint))
			{
				transform = true;
			}
			else if (subnode.hasFn(MFn::kMesh))
			{
				*childIndex = i;
				return (kNodeTypeGeometry);
			}
			else if (subnode.hasFn(MFn::kLight))
			{
				if ((subnode.hasFn(MFn::kDirectionalLight)) || (subnode.hasFn(MFn::kPointLight)) || (subnode.hasFn(MFn::kSpotLight)))
				{
					*childIndex = i;
					return (kNodeTypeLight);
				}
			}
			else if (subnode.hasFn(MFn::kCamera))
			{
				MFnCamera camera(subnode);
				if ((!camera.isOrtho()) && (dagNode.name() != "persp"))
				{
					*childIndex = i;
					return (kNodeTypeCamera);
				}
			}
		}

		if (transform)
		{
			return (kNodeTypeNode);
		}
	}

	return (kNodeTypeNone);
}

MFnSkinCluster *OpenGexExport::GetSkinCluster(const MObject& node)
{
	// This function locates the skin cluster for a geometry node if it has one.
	// (The calling code is responsible for deleting the returned object.)

	MStatus		status;

	MPlug plug = MFnDependencyNode(node).findPlug("inMesh", true, &status);
	if (status == MStatus::kSuccess)
	{
		MItDependencyGraph iterator(plug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kBreadthFirst, MItDependencyGraph::kPlugLevel);
		while (!iterator.isDone())
		{
			MObject object = iterator.currentItem();
			if (object.hasFn(MFn::kSkinClusterFilter))
			{
				return (new MFnSkinCluster(object));
			}

			iterator.next();
		}
	}

	return (nullptr);
}

bool OpenGexExport::FindSkinClusterInputGeometry(const MFnSkinCluster *skin, MObject *object)
{
	MStatus		status;

	MPlug inputGeometryPlug = skin->findPlug("inputGeometry", true, &status);
	if (status == MStatus::kSuccess)
	{
		MPlugArray		sourceArray;

		if (inputGeometryPlug.connectedTo(sourceArray, true, false))
		{
			unsigned int sourceCount = sourceArray.length();
			for (unsigned int i = 0; i < sourceCount; i++)
			{
				sourceArray[i].getValue(*object);
				if (object->hasFn(MFn::kMesh))
				{
					return (true);
				}
			}
		}
	}

	return (false);
}

MFnBlendShapeDeformer *OpenGexExport::GetBlendShapeDeformer(const MObject& node, unsigned int *geometryIndex)
{
	// This function locates the blend shape deformer for a geometry node if it has one.
	// (The calling code is responsible for deleting the returned object.)

	MStatus		status;

	MPlug plug = MFnDependencyNode(node).findPlug("inMesh", true, &status);
	if (status == MStatus::kSuccess)
	{
		MItDependencyGraph iterator(plug, MFn::kInvalid, MItDependencyGraph::kUpstream, MItDependencyGraph::kBreadthFirst, MItDependencyGraph::kPlugLevel);
		while (!iterator.isDone())
		{
			MObject object = iterator.currentItem();
			if (object.hasFn(MFn::kBlendShape))
			{
				MFnBlendShapeDeformer *deformer = new MFnBlendShapeDeformer(object);

				MPlug outputPlug = deformer->findPlug("outputGeometry", true, &status);
				if (status == MStatus::kSuccess)
				{
					unsigned int elementCount = outputPlug.numElements();
					for (unsigned int i = 0; i < elementCount; i++)
					{
						MPlug element = outputPlug.elementByPhysicalIndex(i, &status);
						if (status == MStatus::kSuccess)
						{
							MPlugArray		destArray;

							if (element.connectedTo(destArray, false, true))
							{
								unsigned int destCount = destArray.length();
								for (unsigned int j = 0; j < destCount; j++)
								{
									if (destArray[j].node() == node)
									{
										if (geometryIndex)
										{
											*geometryIndex = element.logicalIndex();
										}
										
										return (deformer);
									}
								}
							}
						}
					}
				}
				
				delete deformer;
				break;
			}

			iterator.next();
		}
	}

	return (nullptr);
}

bool OpenGexExport::FindBlendShapeDeformerInputGeometry(const MFnBlendShapeDeformer *deformer, unsigned int geometryIndex, MObject *object)
{
	MStatus		status;

	MPlug inputPlug = deformer->findPlug("input", true, &status);
	if (status == MStatus::kSuccess)
	{
		MPlug plug = inputPlug.elementByLogicalIndex(geometryIndex);
		unsigned int childCount = plug.numChildren();
		for (unsigned int i = 0; i < childCount; i++)
		{
			MPlug p = plug.child(i);
			if (MFnAttribute(p.attribute()).shortName() == "ig")
			{
				MPlugArray		sourceArray;

				if (p.connectedTo(sourceArray, true, false))
				{
					unsigned int sourceCount = sourceArray.length();
					for (unsigned int i = 0; i < sourceCount; i++)
					{
						sourceArray[i].getValue(*object);
						if (object->hasFn(MFn::kMesh))
						{
							return (true);
						}
					}
				}

				break;
			}
		}
	}

	return (false);
}

NodeReference *OpenGexExport::FindNode(const MObject& node) const
{
	int count = (int) nodeArray->size();
	if (count != 0)
	{
		NodeReference *nodeRef = &nodeArray->front();
		for (int i = 0; i < count; i++)
		{
			if (nodeRef->node == node)
			{
				return (nodeRef);
			}

			nodeRef++;
		}
	}

	return (nullptr);
}

ObjectReference *OpenGexExport::FindObject(std::vector<ObjectReference> *array, const MObject& object)
{
	int count = (int) array->size();
	if (count != 0)
	{
		ObjectReference *objectRef = &array->front();
		for (int i = 0; i < count; i++)
		{
			if (objectRef->object == object)
			{
				return (objectRef);
			}

			objectRef++;
		}
	}

	return (nullptr);
}

MaterialReference *OpenGexExport::FindMaterial(const MObject& material)
{
	int count = (int) materialArray->size();
	if (count != 0)
	{
		MaterialReference *materialRef = &materialArray->front();
		for (int i = 0; i < count; i++)
		{
			if (materialRef->material == material)
			{
				return (materialRef);
			}

			materialRef++;
		}
	}

	return (nullptr);
}

TextureReference *OpenGexExport::FindTexture(const MObject& texture)
{
	int count = (int) textureArray->size();
	if (count != 0)
	{
		TextureReference *textureRef = &textureArray->front();
		for (int i = 0; i < count; i++)
		{
			if (textureRef->texture == texture)
			{
				return (textureRef);
			}

			textureRef++;
		}
	}

	return (nullptr);
}

int OpenGexExport::GetLocalIndex(int index, const MIntArray& globalIndexArray)
{
	unsigned int count = globalIndexArray.length();
	for (unsigned int i = 0; i < count; i++)
	{
		if (globalIndexArray[i] == index)
		{
			return (i);
		}
	}

	return (0);
}

ExportVertex *OpenGexExport::DeindexMesh(MFnMesh *mesh, const MFnMesh *baseMesh, int *exportTriangleCount, int *exportColorCount, int *exportTexcoordCount, int **polygonIndexArray)
{
	// This function deindexes all vertex positions, colors, and texcoords.
	// Three separate ExportVertex structures are created for each triangle.

	MIntArray			triangleCountArray;
	MIntArray			triangulationIndexArray;
	MFloatPointArray	vertexArray;
	MFloatVectorArray	normalArray;
	MStringArray		colorSetNameArray;
	MStringArray		uvSetNameArray;

	mesh->getTriangles(triangleCountArray, triangulationIndexArray);

	int triangleCount = 0;
	int indexCount = 0;

	unsigned int polygonCount = triangleCountArray.length();
	for (unsigned int i = 0; i < polygonCount; i++)
	{
		MIntArray	vertexIndexArray;

		int count = triangleCountArray[i];
		triangleCount += count;

		mesh->getPolygonVertices(i, vertexIndexArray);

		count *= 3;
		for (int j = 0; j < count; j++)
		{
			triangulationIndexArray[indexCount] = GetLocalIndex(triangulationIndexArray[indexCount], vertexIndexArray);
			indexCount++;
		}
	}

	// Fill in a table that maps triangle indexes to polygon indexes.
	// This is used to determine what shader is applied to each triangle.

	int *polygonIndex = new int[triangleCount];
	*polygonIndexArray = polygonIndex;

	for (unsigned int i = 0; i < polygonCount; i++)
	{
		int count = triangleCountArray[i];
		for (int j = 0; j < count; j++)
		{
			polygonIndex[j] = i;
		}

		polygonIndex += count;
	}

	*exportTriangleCount = triangleCount;
	ExportVertex *exportVertex = new ExportVertex[triangleCount * 3];

	baseMesh->getPoints(vertexArray);
	baseMesh->getNormals(normalArray);

	int base = 0;
	ExportVertex *ev = exportVertex;
	for (unsigned int i = 0; i < polygonCount; i++)
	{
		MIntArray	vertexIndexArray;
		MIntArray	normalIndexArray;

		mesh->getPolygonVertices(i, vertexIndexArray);
		mesh->getFaceNormalIds(i, normalIndexArray);

		int count = triangleCountArray[i];
		for (int j = 0; j < count; j++)
		{
			unsigned int t1 = triangulationIndexArray[base];
			unsigned int t2 = triangulationIndexArray[base + 1];
			unsigned int t3 = triangulationIndexArray[base + 2];

			unsigned int k1 = vertexIndexArray[t1];
			unsigned int k2 = vertexIndexArray[t2];
			unsigned int k3 = vertexIndexArray[t3];

			ev[0].vertexIndex = k1;
			ev[1].vertexIndex = k2;
			ev[2].vertexIndex = k3;

			ev[0].position = vertexArray[k1];
			ev[1].position = vertexArray[k2];
			ev[2].position = vertexArray[k3];

			k1 = normalIndexArray[t1];
			k2 = normalIndexArray[t2];
			k3 = normalIndexArray[t3];

			ev[0].normalIndex = k1;
			ev[1].normalIndex = k2;
			ev[2].normalIndex = k3;

			ev[0].normal = normalArray[k1];
			ev[1].normal = normalArray[k2];
			ev[2].normal = normalArray[k3];

			base += 3;
			ev += 3;
		}
	}

	int colorSetCount = mesh->numColorSets();
	if (colorSetCount > kMaxVertexColorCount)
	{
		colorSetCount = kMaxVertexColorCount;
	}

	*exportColorCount = colorSetCount;

	mesh->getColorSetNames(colorSetNameArray);
	for (int m = 0; m < colorSetCount; m++)
	{
		MColorArray		colorArray;

		MString colorSetName = colorSetNameArray[m];

		mesh->getColors(colorArray, &colorSetName);
		if (colorArray.length() != 0)
		{
			int base = 0;
			ExportVertex *ev = exportVertex;
			for (unsigned int i = 0; i < polygonCount; i++)
			{
				int count = triangleCountArray[i];
				for (int j = 0; j < count; j++)
				{
					int k1 = 0;
					int k2 = 0;
					int k3 = 0;

					unsigned int t1 = triangulationIndexArray[base];
					unsigned int t2 = triangulationIndexArray[base + 1];
					unsigned int t3 = triangulationIndexArray[base + 2];

					mesh->getColorIndex(i, t1, k1, &colorSetName);
					mesh->getColorIndex(i, t2, k2, &colorSetName);
					mesh->getColorIndex(i, t3, k3, &colorSetName);

					ev[0].color[m] = colorArray[(k1 >= 0) ? k1 : 0];
					ev[1].color[m] = colorArray[(k2 >= 0) ? k2 : 0];
					ev[2].color[m] = colorArray[(k3 >= 0) ? k3 : 0];

					base += 3;
					ev += 3;
				}
			}
		}
	}

	int uvSetCount = mesh->numUVSets();
	if (uvSetCount > kMaxTexcoordCount)
	{
		uvSetCount = kMaxTexcoordCount;
	}

	*exportTexcoordCount = uvSetCount;

	mesh->getUVSetNames(uvSetNameArray);
	for (int m = 0; m < uvSetCount; m++)
	{
		MFloatArray		ucoordArray;
		MFloatArray		vcoordArray;

		MString uvSetName = uvSetNameArray[m];

		mesh->getUVs(ucoordArray, vcoordArray, &uvSetName);
		if (ucoordArray.length() != 0)
		{
			int base = 0;
			ExportVertex *ev = exportVertex;
			for (unsigned int i = 0; i < polygonCount; i++)
			{
				int count = triangleCountArray[i];
				for (int j = 0; j < count; j++)
				{
					int k1 = 0;
					int k2 = 0;
					int k3 = 0;

					unsigned int t1 = triangulationIndexArray[base];
					unsigned int t2 = triangulationIndexArray[base + 1];
					unsigned int t3 = triangulationIndexArray[base + 2];

					mesh->getPolygonUVid(i, t1, k1, &uvSetName);
					mesh->getPolygonUVid(i, t2, k2, &uvSetName);
					mesh->getPolygonUVid(i, t3, k3, &uvSetName);

					ev[0].texcoord[m][0] = ucoordArray[k1];
					ev[0].texcoord[m][1] = vcoordArray[k1];
					ev[1].texcoord[m][0] = ucoordArray[k2];
					ev[1].texcoord[m][1] = vcoordArray[k2];
					ev[2].texcoord[m][0] = ucoordArray[k3];
					ev[2].texcoord[m][1] = vcoordArray[k3];

					base += 3;
					ev += 3;
				}
			}
		}

		if (m != 0)
		{
			MObjectArray	objectArray;

			if (mesh->getAssociatedUVSetTextures(uvSetName, objectArray) == MStatus::kSuccess)
			{
				unsigned int count = objectArray.length();
				for (unsigned int i = 0; i < count; i++)
				{
					const MObject& texture = objectArray[i];
					if (!FindTexture(texture))
					{
						textureArray->push_back(TextureReference(texture, m));
					}
				}
			}
		}
	}

	ev = exportVertex;
	int exportCount = triangleCount * 3;
	for (int i = 0; i < exportCount; i++)
	{
		ev[i].Hash();
	}

	return (exportVertex);
}

int OpenGexExport::FindExportVertex(const std::vector<int>& bucket, const ExportVertex *exportVertex, const ExportVertex& vertex)
{
	int size = (int) bucket.size();
	for (int i = 0; i < size; i++)
	{
		int index = bucket[i];
		if (exportVertex[index] == vertex)
		{
			return (index);
		}
	}

	return (-1);
}

int OpenGexExport::UnifyVertices(int vertexCount, const ExportVertex *exportVertex, ExportVertex *unifiedVertex, int *indexTable)
{
	// This function looks for identical vertices having exactly the same position, normal,
	// color, and texcoords. Duplicate vertices are unified, and a new index table is returned.

	int bucketCount = vertexCount >> 5;
	if (bucketCount > 1)
	{
		// Round down to nearest power of two by clearing the lowest
		// one bit until there's only a single one bit left. There are
		// faster ways of doing this, but they aren't as portable.

		for (;;)
		{
			int count = bucketCount & (bucketCount - 1);
			if (count == 0)
			{
				break;
			}

			bucketCount = count;
		}
	}
	else
	{
		bucketCount = 1;
	}

	std::vector<int> *hashTable = new std::vector<int>[bucketCount];
	int unifiedCount = 0;

	for (int i = 0; i < vertexCount; i++)
	{
		unsigned int bucket = exportVertex[i].hash & (bucketCount - 1);
		int index = FindExportVertex(hashTable[bucket], exportVertex, exportVertex[i]);
		if (index < 0)
		{
			indexTable[i] = unifiedCount;
			unifiedVertex[unifiedCount] = exportVertex[i];
			unifiedCount++;

			hashTable[bucket].push_back(i);
		}
		else
		{
			indexTable[i] = indexTable[index];
		}
	}

	delete[] hashTable;
	return (unifiedCount);
}

void OpenGexExport::ProcessNode(const MDagPath& dagPath, const MSelectionList *exportList)
{
	MObject node = dagPath.node();

	int index = 0;
	int type = GetNodeType(node, &index);

	if (type != kNodeTypeNone)
	{
		MFnDagNode dagNode(node);
		if ((dagNode.canBeWritten()) || (dagNode.isShared()))
		{
			if ((!exportList) || (exportList->hasItem(dagPath)))
			{
				int size = (int) nodeArray->size();
				nodeArray->push_back(NodeReference(node, type, index, (std::string("node") += std::to_string(size + 1)).c_str()));
			}

			unsigned int subnodeCount = dagNode.childCount();
			for (unsigned int i = 0; i < subnodeCount; i++)
			{
				MDagPath childPath(dagPath);
				childPath.push(dagPath.child(i));
				ProcessNode(childPath, exportList);
			}
		}
	}
}

void OpenGexExport::ProcessSkinnedMeshes(void)
{
	int count = (int) nodeArray->size();
	if (count != 0)
	{
		NodeReference *nodeRef = &nodeArray->front();
		for (int i = 0; i < count; i++)
		{
			if (nodeRef->nodeType == kNodeTypeGeometry)
			{
				MObject object = MFnDagNode(nodeRef->node).child(nodeRef->childIndex);

				MFnSkinCluster *skin = GetSkinCluster(object);
				if (skin)
				{
					MDagPathArray	dagPathArray;

					int boneCount = skin->influenceObjects(dagPathArray);
					for (int k = 0; k < boneCount; k++)
					{
						// If a node is used as a bone, then we force its type to be a bone.

						MObject node = dagPathArray[k].node();
						NodeReference *boneRef = FindNode(node);
						if (boneRef)
						{
							boneRef->nodeType = kNodeTypeBone;
						}
					}

					delete skin;
				}
			}

			nodeRef++;
		}
	}
}

bool OpenGexExport::AnimationPresent(const MFnAnimCurve& animCurve)
{
	MFnAnimCurve::TangentValue		x1, x2, y1, y2;

	animCurve.getTangent(0, x1, y1, true);
	animCurve.getTangent(0, x2, y2, true);

	if ((fabs(y1) > kExportEpsilon) || (fabs(y2) > kExportEpsilon))
	{
		return (true);
	}

	double key1 = animCurve.value(0);

	int keyCount = animCurve.numKeys();
	for (int i = 1; i < keyCount; i++)
	{
		double key2 = animCurve.value(i);
		if (fabs(key2 - key1) > kExportEpsilon)
		{
			return (true);
		}

		animCurve.getTangent(i, x1, y1, true);
		animCurve.getTangent(i, x2, y2, true);

		if ((fabs(y1) > kExportEpsilon) || (fabs(y2) > kExportEpsilon))
		{
			return (true);
		}
	}

	return (false);
}

void OpenGexExport::ExportKeyTimes(const MFnAnimCurve& animCurve)
{
	IndentWrite("Key {float {");

	int keyCount = animCurve.numKeys();
	for (int i = 0;;)
	{
		MTime time = animCurve.time(i);
		WriteFloat(float(time.as(MTime::kSeconds)));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportKeyTimeControlPoints(const MFnAnimCurve& animCurve)
{
	IndentWrite("Key (kind = \"-control\") {float {");

	int keyCount = animCurve.numKeys();
	for (int i = 0;;)
	{
		MFnAnimCurve::TangentValue		x, y;

		MTime time = animCurve.time(i);
		animCurve.getTangent(i, x, y, true);
		WriteFloat(float(time.as(MTime::kSeconds) - x * 0.333333F));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
	IndentWrite("Key (kind = \"+control\") {float {");

	for (int i = 0;;)
	{
		MFnAnimCurve::TangentValue		x, y;

		MTime time = animCurve.time(i);
		animCurve.getTangent(i, x, y, false);
		WriteFloat(float(time.as(MTime::kSeconds) + x * 0.333333F));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportKeyValues(const MFnAnimCurve& animCurve, float scale)
{
	IndentWrite("Key {float {");

	int keyCount = animCurve.numKeys();
	for (int i = 0;;)
	{
		double value = animCurve.value(i);
		WriteFloat(float(value) * scale);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportKeyValueControlPoints(const MFnAnimCurve& animCurve, float scale)
{
	IndentWrite("Key (kind = \"-control\") {float {");

	int keyCount = animCurve.numKeys();
	for (int i = 0;;)
	{
		MFnAnimCurve::TangentValue		x, y;

		double value = animCurve.value(i);
		animCurve.getTangent(i, x, y, true);

		if (!animCurve.isWeighted())
		{
			double t1 = animCurve.time((i > 0) ? i - 1 : 0).as(MTime::kSeconds);
			double t2 = animCurve.time(i).as(MTime::kSeconds);

			y = (fabs(x) > FLT_MIN) ? y * (t2 - t1) / x : 0.0F;
		}

		WriteFloat(float(value - y * 0.333333F) * scale);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
	IndentWrite("Key (kind = \"+control\") {float {");

	for (int i = 0;;)
	{
		MFnAnimCurve::TangentValue		x, y;

		double value = animCurve.value(i);
		animCurve.getTangent(i, x, y, false);

		if (!animCurve.isWeighted())
		{
			double t1 = animCurve.time(i).as(MTime::kSeconds);
			double t2 = animCurve.time((i < keyCount - 1) ? i + 1 : keyCount - 1).as(MTime::kSeconds);

			y = (fabs(x) > FLT_MIN) ? y * (t2 - t1) / x : 0.0F;
		}

		WriteFloat(float(value + y * 0.333333F) * scale);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportAnimationTrack(const MFnAnimCurve& animCurve, const char *target, bool newline, float scale)
{
	// This function exports a single animation track. The curve type for the
	// Time structure depends on whether the animation curve is weighted.

	IndentWrite("Track (target = %", 0, newline);
	Write(target);
	Write(")\n");
	IndentWrite("{\n");
	indentLevel++;

	if (!animCurve.isWeighted())
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes(animCurve);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"bezier\")\n", -1);
		IndentWrite("{\n", -1);

		ExportKeyValues(animCurve, scale);
		ExportKeyValueControlPoints(animCurve, scale);

		indentLevel--;
		IndentWrite("}\n");
	}
	else
	{
		IndentWrite("Time (curve = \"bezier\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes(animCurve);
		ExportKeyTimeControlPoints(animCurve);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"bezier\")\n", -1);
		IndentWrite("{\n", -1);

		ExportKeyValues(animCurve, scale);
		ExportKeyValueControlPoints(animCurve, scale);

		indentLevel--;
		IndentWrite("}\n");
	}

	indentLevel--;
	IndentWrite("}\n");
}

void OpenGexExport::ExportTransform(const MObject& node, const MObject& parent)
{
	// This function determines whether any animation needs to be exported
	// and writes the node transform in the appropriate form. This is followed
	// by the animation tracks.

	MPlugArray	plugArray;

	MFnAnimCurve *posAnimCurve[3] = {nullptr, nullptr, nullptr};
	MFnAnimCurve *rotAnimCurve[3] = {nullptr, nullptr, nullptr};
	MFnAnimCurve *sclAnimCurve[3] = {nullptr, nullptr, nullptr};

	bool positionAnimated = false;
	bool rotationAnimated = false;
	bool scaleAnimated = false;
	bool posAnimated[3] = {false, false, false};
	bool rotAnimated[3] = {false, false, false};
	bool sclAnimated[3] = {false, false, false};

	MFnTransform transformNode(node);

	transformNode.getConnections(plugArray);
	unsigned int count = plugArray.length();

	for (unsigned int i = 0; i < count; i++)
	{
		MPlugArray		sourceArray;

		const MPlug& plug = plugArray[i];
		MString plugName = plug.partialName();

		if (plug.connectedTo(sourceArray, true, false))
		{
			unsigned int sourceCount = sourceArray.length();
			if (sourceCount != 0)
			{
				MObject source = sourceArray[0].node();
				if (source.hasFn(MFn::kAnimCurve))
				{
					if ((plugName == "tx") && (!posAnimCurve[0]))
					{
						posAnimCurve[0] = new MFnAnimCurve(source);
						if (AnimationPresent(*posAnimCurve[0]))
						{
							posAnimated[0] = true;
						}
					}
					else if ((plugName == "ty") && (!posAnimCurve[1]))
					{
						posAnimCurve[1] = new MFnAnimCurve(source);
						if (AnimationPresent(*posAnimCurve[1]))
						{
							posAnimated[1] = true;
						}
					}
					else if ((plugName == "tz") && (!posAnimCurve[2]))
					{
						posAnimCurve[2] = new MFnAnimCurve(source);
						if (AnimationPresent(*posAnimCurve[2]))
						{
							posAnimated[2] = true;
						}
					}
					else if ((plugName == "rx") && (!rotAnimCurve[0]))
					{
						rotAnimCurve[0] = new MFnAnimCurve(source);
						if (AnimationPresent(*rotAnimCurve[0]))
						{
							rotAnimated[0] = true;
						}
					}
					else if ((plugName == "ry") && (!rotAnimCurve[1]))
					{
						rotAnimCurve[1] = new MFnAnimCurve(source);
						if (AnimationPresent(*rotAnimCurve[1]))
						{
							rotAnimated[1] = true;
						}
					}
					else if ((plugName == "rz") && (!rotAnimCurve[2]))
					{
						rotAnimCurve[2] = new MFnAnimCurve(source);
						if (AnimationPresent(*rotAnimCurve[2]))
						{
							rotAnimated[2] = true;
						}
					}
					else if ((plugName == "sx") && (!sclAnimCurve[0]))
					{
						sclAnimCurve[0] = new MFnAnimCurve(source);
						if (AnimationPresent(*sclAnimCurve[0]))
						{
							sclAnimated[0] = true;
						}
					}
					else if ((plugName == "sy") && (!sclAnimCurve[1]))
					{
						sclAnimCurve[1] = new MFnAnimCurve(source);
						if (AnimationPresent(*sclAnimCurve[1]))
						{
							sclAnimated[1] = true;
						}
					}
					else if ((plugName == "sz") && (!sclAnimCurve[2]))
					{
						sclAnimCurve[2] = new MFnAnimCurve(source);
						if (AnimationPresent(*sclAnimCurve[2]))
						{
							sclAnimated[2] = true;
						}
					}
				}
			}
		}
	}

	positionAnimated = posAnimated[0] | posAnimated[1] | posAnimated[2];
	rotationAnimated = rotAnimated[0] | rotAnimated[1] | rotAnimated[2];
	scaleAnimated = sclAnimated[0] | sclAnimated[1] | sclAnimated[2];

	if ((!positionAnimated) && (!rotationAnimated) && (!scaleAnimated))
	{
		// If there's no keyframe animation at all, then write the node transform as a single 4x4 matrix.

		IndentWrite("Transform");
		IndentWrite("{\n", 0, true);
		indentLevel++;

		IndentWrite("float[16]\n");
		IndentWrite("{\n");
		WriteMatrix(transformNode.transformationMatrix());
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");
	}
	else
	{
		static const char *const subtranslationName[3] =
		{
			"xpos", "ypos", "zpos"
		};

		static const char *const subrotationName[3] =
		{
			"xrot", "yrot", "zrot"
		};

		static const char *const subscaleName[3] =
		{
			"xscl", "yscl", "zscl"
		};

		static const char *const axisName[3] =
		{
			"x", "y", "z"
		};

		static const char eulerAxis[6][3] =
		{
			{0, 1, 2}, {1, 2, 0}, {2, 0, 1}, {0, 2, 1}, {1, 0, 2}, {2, 1, 0}
		};

		MEulerRotation	eulerRotation;
		double			scale[3];
		double			shear[3];

		bool structFlag = false;

		MVector translation = transformNode.getTranslation(MSpace::kTransform);
		if (positionAnimated)
		{
			// When the position is animated, write the x, y, and z components separately
			// so they can be targeted by different tracks having different sets of keys.

			for (int i = 0; i < 3; i++)
			{
				float pos = float(translation[i]);

				if ((posAnimated[i]) || (fabs(pos) > kExportEpsilon))
				{
					IndentWrite("Translation %", 0, structFlag);
					Write(subtranslationName[i]);
					Write(" (kind = \"");
					Write(axisName[i]);
					Write("\")\n");
					IndentWrite("{\n");
					IndentWrite("float {", 1);
					WriteHexFloat(pos);
					Write("}\t\t// ");
					WriteFloat(pos);
					IndentWrite("}\n", 0, true);

					structFlag = true;
				}
			}
		}
		else if ((fabs(translation.x) > kExportEpsilon) || (fabs(translation.y) > kExportEpsilon) || (fabs(translation.z) > kExportEpsilon))
		{
			IndentWrite("Translation\n");
			IndentWrite("{\n");
			IndentWrite("float[3] {", 1);
			WriteHexVector(translation);
			Write("}\t\t// ");
			WriteVector(translation);
			IndentWrite("}\n", 0, true);

			structFlag = true;
		}

		if (!node.hasFn(MFn::kJoint))
		{
			MVector rotatePivotTranslation = transformNode.rotatePivotTranslation(MSpace::kTransform);
			if ((fabs(rotatePivotTranslation.x) > kExportEpsilon) || (fabs(rotatePivotTranslation.y) > kExportEpsilon) || (fabs(rotatePivotTranslation.z) > kExportEpsilon))
			{
				IndentWrite("Translation\t\t// rotate pivot translation\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[3] {", 1);
				WriteHexVector(rotatePivotTranslation);
				Write("}\t\t// ");
				WriteVector(rotatePivotTranslation);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			MVector rotatePivot = transformNode.rotatePivot(MSpace::kTransform);
			bool rotatePivotPresent = ((fabs(rotatePivot.x) > kExportEpsilon) || (fabs(rotatePivot.y) > kExportEpsilon) || (fabs(rotatePivot.z) > kExportEpsilon));

			if (rotatePivotPresent)
			{
				IndentWrite("Translation\t\t// rotate pivot point\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[3] {", 1);
				WriteHexVector(rotatePivot);
				Write("}\t\t// ");
				WriteVector(rotatePivot);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			if (rotationAnimated)
			{
				// When the rotation is animated, write three separate Euler angle rotations
				// so they can be targeted by different tracks having different sets of keys.

				transformNode.getRotation(eulerRotation);
				MEulerRotation::RotationOrder eulerOrder = eulerRotation.order;

				for (int i = 2; i >= 0; i--)
				{
					int axis = eulerAxis[eulerOrder][i];
					float angle = float(eulerRotation[axis]);

					if ((rotAnimated[axis]) || (fabs(angle) > kExportEpsilon))
					{
						IndentWrite("Rotation %", 0, structFlag);
						Write(subrotationName[axis]);
						Write(" (kind = \"");
						Write(axisName[axis]);
						Write("\")\n");
						IndentWrite("{\n");

						IndentWrite("float {", 1);
						WriteHexFloat(angle);
						Write("}\t\t// ");
						WriteFloat(angle);
						IndentWrite("}\n", 0, true);

						structFlag = true;
					}
				}
			}
			else
			{
				// When the rotation is not animated, write it as a single quaternion.

				MQuaternion		quaternion;

				transformNode.getRotation(quaternion);

				IndentWrite("Rotation (kind = \"quaternion\")\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuaternion(quaternion);
				Write("}\t\t// ");
				WriteQuaternion(quaternion);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			MQuaternion rotateOrientation = transformNode.rotateOrientation(MSpace::kTransform);
			if ((fabs(rotateOrientation.x) > kExportEpsilon) || (fabs(rotateOrientation.y) > kExportEpsilon) || (fabs(rotateOrientation.z) > kExportEpsilon) || (fabs(rotateOrientation.w - 1.0) > kExportEpsilon))
			{
				IndentWrite("Rotation (kind = \"quaternion\")\t\t// rotation orientation\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuaternion(rotateOrientation);
				Write("}\t\t// ");
				WriteQuaternion(rotateOrientation);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			if (rotatePivotPresent)
			{
				IndentWrite("Translation\t\t// inverse rotate pivot point\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[3] {", 1);
				WriteHexVector(-rotatePivot);
				Write("}\t\t// ");
				WriteVector(-rotatePivot);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			MVector scalePivotTranslation = transformNode.scalePivotTranslation(MSpace::kTransform);
			if ((fabs(scalePivotTranslation.x) > kExportEpsilon) || (fabs(scalePivotTranslation.y) > kExportEpsilon) || (fabs(scalePivotTranslation.z) > kExportEpsilon))
			{
				IndentWrite("Translation\t\t// scale pivot translation\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[3] {", 1);
				WriteHexVector(scalePivotTranslation);
				Write("}\t\t// ");
				WriteVector(scalePivotTranslation);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			transformNode.getShear(shear);
			bool shearPresent = ((fabs(shear[0]) > kExportEpsilon) || (fabs(shear[1]) > kExportEpsilon) || (fabs(shear[2]) > kExportEpsilon));

			transformNode.getScale(scale);
			bool scalePresent = ((scaleAnimated) || (fabs(scale[0] - 1.0) > kExportEpsilon) || (fabs(scale[1] - 1.0) > kExportEpsilon) || (fabs(scale[2] - 1.0) > kExportEpsilon));

			if (shearPresent | scalePresent)
			{
				MVector scalePivot = transformNode.scalePivot(MSpace::kTransform);
				bool scalePivotPresent = ((fabs(scalePivot.x) > kExportEpsilon) || (fabs(scalePivot.y) > kExportEpsilon) || (fabs(scalePivot.z) > kExportEpsilon));

				if (scalePivotPresent)
				{
					IndentWrite("Translation\t\t// scale pivot\n", 0, structFlag);
					IndentWrite("{\n");
					IndentWrite("float[3] {", 1);
					WriteHexVector(scalePivot);
					Write("}\t\t// ");
					WriteVector(scalePivot);
					IndentWrite("}\n", 0, true);

					structFlag = true;
				}

				if (shearPresent)
				{
					MMatrix		shearMatrix;

					shearMatrix.setToIdentity();
					shearMatrix(1,0) = shear[0];
					shearMatrix(2,0) = shear[1];
					shearMatrix(2,1) = shear[2];

					IndentWrite("Transform\n", 0, structFlag);
					IndentWrite("{\n");
					indentLevel++;

					IndentWrite("float[16]");
					IndentWrite("{\n");
					WriteMatrix(shearMatrix);
					IndentWrite("}\n");

					indentLevel--;
					IndentWrite("}\n");

					structFlag = true;
				}

				if (scalePresent)
				{
					if (scaleAnimated)
					{
						// When the scale is animated, write the x, y, and z components separately
						// so they can be targeted by different tracks having different sets of keys.

						for (int i = 0; i < 3; i++)
						{
							float scl = float(scale[i]);

							if ((sclAnimated[i]) || (fabs(scl) - 1.0 > kExportEpsilon))
							{
								IndentWrite("Scale %", 0, structFlag);
								Write(subscaleName[i]);
								Write(" (kind = \"");
								Write(axisName[i]);
								Write("\")\n");
								IndentWrite("{\n");
								IndentWrite("float {", 1);
								WriteHexFloat(scl);
								Write("}\t\t// ");
								WriteFloat(scl);
								IndentWrite("}\n", 0, true);

								structFlag = true;
							}
						}
					}
					else
					{
						MVector scaleVector(scale[0], scale[1], scale[2]);

						IndentWrite("Scale\n", 0, structFlag);
						IndentWrite("{\n");
						IndentWrite("float[3] {", 1);
						WriteHexVector(scaleVector);
						Write("}\t\t// ");
						WriteVector(scaleVector);
						IndentWrite("}\n", 0, true);

						structFlag = true;
					}
				}

				if (scalePivotPresent)
				{
					IndentWrite("Translation\t\t// inverse scale pivot", 0, structFlag);
					IndentWrite("{\n", 0, true);
					IndentWrite("float[3] {", 1);
					WriteHexVector(-scalePivot);
					Write("}\t\t// ");
					WriteVector(-scalePivot);
					IndentWrite("}\n", 0, true);

					structFlag = true;
				}
			}
		}
		else
		{
			MQuaternion		jointOrientation;
			MQuaternion		scaleOrientation;

			if (parent.hasFn(MFn::kTransform))
			{
				MFnTransform(parent).getScale(scale);
				if ((fabs(scale[0] - 1.0) > kExportEpsilon) || (fabs(scale[1] - 1.0) > kExportEpsilon) || (fabs(scale[2] - 1.0) > kExportEpsilon))
				{
					MVector scaleVector(1.0 / scale[0], 1.0 / scale[1], 1.0 / scale[2]);

					IndentWrite("Scale\t\t// inverse parent scale\n", 0, structFlag);
					IndentWrite("{\n");
					IndentWrite("float[3] {", 1);
					WriteHexVector(scaleVector);
					Write("}\t\t// ");
					WriteVector(scaleVector);
					IndentWrite("}\n", 0, true);

					structFlag = true;
				}
			}

			MFnIkJoint jointNode(node);

			jointNode.getOrientation(jointOrientation);
			if ((fabs(jointOrientation.x) > kExportEpsilon) || (fabs(jointOrientation.y) > kExportEpsilon) || (fabs(jointOrientation.z) > kExportEpsilon) || (fabs(jointOrientation.w - 1.0) > kExportEpsilon))
			{
				IndentWrite("Rotation (kind = \"quaternion\")\t\t// joint orientation\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuaternion(jointOrientation);
				Write("}\t\t// ");
				WriteQuaternion(jointOrientation);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			if (rotationAnimated)
			{
				// When the rotation is animated, write three separate Euler angle rotations
				// so they can be targeted by different tracks having different sets of keys.

				jointNode.getRotation(eulerRotation);
				MEulerRotation::RotationOrder eulerOrder = eulerRotation.order;

				for (int i = 2; i >= 0; i--)
				{
					int axis = eulerAxis[eulerOrder][i];
					float angle = float(eulerRotation[axis]);

					if ((rotAnimated[axis]) || (fabs(angle) > kExportEpsilon))
					{
						IndentWrite("Rotation %", 0, structFlag);
						Write(subrotationName[axis]);
						Write(" (kind = \"");
						Write(axisName[axis]);
						Write("\")\n");
						IndentWrite("{\n");

						IndentWrite("float {", 1);
						WriteHexFloat(angle);
						Write("}\t\t// ");
						WriteFloat(angle);
						IndentWrite("}\n", 0, true);

						structFlag = true;
					}
				}
			}
			else
			{
				// When the rotation is not animated, write it as a single quaternion.

				MQuaternion		quaternion;

				jointNode.getRotation(quaternion);

				IndentWrite("Rotation (kind = \"quaternion\")\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuaternion(quaternion);
				Write("}\t\t// ");
				WriteQuaternion(quaternion);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			jointNode.getScaleOrientation(scaleOrientation);
			if ((fabs(scaleOrientation.x) > kExportEpsilon) || (fabs(scaleOrientation.y) > kExportEpsilon) || (fabs(scaleOrientation.z) > kExportEpsilon) || (fabs(scaleOrientation.w - 1.0) > kExportEpsilon))
			{
				IndentWrite("Rotation (kind = \"quaternion\")\t\t// scale orientation\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuaternion(scaleOrientation);
				Write("}\t\t// ");
				WriteQuaternion(scaleOrientation);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			jointNode.getScale(scale);
			if (scaleAnimated)
			{
				// When the scale is animated, write the x, y, and z components separately
				// so they can be targeted by different tracks having different sets of keys.

				for (int i = 0; i < 3; i++)
				{
					float scl = float(scale[i]);

					if ((sclAnimated[i]) || (fabs(scl) - 1.0 > kExportEpsilon))
					{
						IndentWrite("Scale %", 0, structFlag);
						Write(subscaleName[i]);
						Write(" (kind = \"");
						Write(axisName[i]);
						Write("\")\n");
						IndentWrite("{\n");
						IndentWrite("float {", 1);
						WriteHexFloat(scl);
						Write("}\t\t// ");
						WriteFloat(scl);
						IndentWrite("}\n", 0, true);

						structFlag = true;
					}
				}
			}
			else if ((fabs(scale[0] - 1.0) > kExportEpsilon) || (fabs(scale[1] - 1.0) > kExportEpsilon) || (fabs(scale[2] - 1.0) > kExportEpsilon))
			{
				MVector scaleVector(scale[0], scale[1], scale[2]);

				IndentWrite("Scale\n", 0, structFlag);
				IndentWrite("{\n");
				IndentWrite("float[3] {", 1);
				WriteHexVector(scaleVector);
				Write("}\t\t// ");
				WriteVector(scaleVector);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}
		}

		// Export the animation tracks.

		IndentWrite("Animation (begin = ", 0, true);
		WriteFloat(float(MAnimControl::animationStartTime().as(MTime::kSeconds)));
		Write(", end = ");
		WriteFloat(float(MAnimControl::animationEndTime().as(MTime::kSeconds)));
		Write(")\n");
		IndentWrite("{\n");
		indentLevel++;

		structFlag = false;

		if (positionAnimated)
		{
			for (int i = 0; i < 3; i++)
			{
				if (posAnimated[i])
				{
					ExportAnimationTrack(*posAnimCurve[i], subtranslationName[i], structFlag);
					structFlag = true;
				}
			}
		}

		if (rotationAnimated)
		{
			for (int i = 0; i < 3; i++)
			{
				if (rotAnimated[i])
				{
					ExportAnimationTrack(*rotAnimCurve[i], subrotationName[i], structFlag);
					structFlag = true;
				}
			}
		}

		if (scaleAnimated)
		{
			for (int i = 0; i < 3; i++)
			{
				if (sclAnimated[i])
				{
					ExportAnimationTrack(*sclAnimCurve[i], subscaleName[i], structFlag);
					structFlag = true;
				}
			}
		}

		indentLevel--;
		IndentWrite("}\n");
	}

	for (int i = 2; i >= 0; i--)
	{
		delete sclAnimCurve[i];
		delete rotAnimCurve[i];
		delete posAnimCurve[i];
	}
}

void OpenGexExport::ExportMaterialRef(const MObject& material, int index)
{
	MaterialReference *materialRef = FindMaterial(material);
	if (!materialRef)
	{
		int size = (int) materialArray->size();
		materialArray->push_back(MaterialReference(material, (std::string("material") += std::to_string(size + 1)).c_str()));
		materialRef = &materialArray->at(size);
	}

	if (index < 0)
	{
		IndentWrite("MaterialRef {ref {$");
	}
	else
	{
		IndentWrite("MaterialRef (index = ");
		WriteInt(index);
		Write(") {ref {$");
	}

	Write(materialRef->structName.c_str());
	Write("}}\n");
}

void OpenGexExport::ExportMorphWeights(const MObject& node, const MFnBlendShapeDeformer *deformer)
{
	MStatus		status;
	MIntArray	weightIndexArray;

	bool animatedFlag = false;

	deformer->weightIndexList(weightIndexArray);
	unsigned int weightCount = weightIndexArray.length();

	bool *weightAnimated = new bool[weightCount];
	MFnAnimCurve **weightAnimCurve = new MFnAnimCurve *[weightCount];
	for (unsigned int k = 0; k < weightCount; k++)
	{
		weightAnimated[k] = false;
		weightAnimCurve[k] = nullptr;
	}

	MPlug weightPlug = deformer->findPlug("w", true, &status);
	if (status == MS::kSuccess)
	{
		for (unsigned int k = 0; k < weightCount; k++)
		{
			MPlugArray		sourceArray;

			int weightIndex = weightIndexArray[k];
			MPlug plug = weightPlug.elementByLogicalIndex(weightIndex);
			if (plug.connectedTo(sourceArray, true, false))
			{
				unsigned int sourceCount = sourceArray.length();
				if (sourceCount != 0)
				{
					MObject source = sourceArray[0].node();
					if (source.hasFn(MFn::kAnimCurve))
					{
						MFnAnimCurve *animCurve = new MFnAnimCurve(source);
						weightAnimCurve[k] = animCurve;
						if (AnimationPresent(*animCurve))
						{
							weightAnimated[k] = true;
							animatedFlag = true;
						}
					}
				}
			}
		}
	}

	IndentWrite("MorphWeight (index = 0) {float {1}}\n", 0, true);

	float envelope = deformer->envelope();

	int morphIndex = 1;
	for (unsigned int k = 0; k < weightCount; k++)
	{
		MObjectArray	targetArray;

		int weightIndex = weightIndexArray[k];
		deformer->getTargets(node, weightIndex, targetArray);

		unsigned int targetCount = targetArray.length();
		for (unsigned int m = 0; m < targetCount; m++)
		{
			IndentWrite("MorphWeight");

			if (animatedFlag)
			{
				Write(" %mw");
				WriteInt(morphIndex);
			}

			Write(" (index = ");
			WriteInt(morphIndex);
			Write(") {float {");
			WriteFloat(deformer->weight(weightIndex) * envelope);
			Write("}}\n");

			morphIndex++;
		}
	}

	if (animatedFlag)
	{
		IndentWrite("Animation (begin = ", 0, true);
		WriteFloat(float(MAnimControl::animationStartTime().as(MTime::kSeconds)));
		Write(", end = ");
		WriteFloat(float(MAnimControl::animationEndTime().as(MTime::kSeconds)));
		Write(")\n");
		IndentWrite("{\n");
		indentLevel++;

		morphIndex = 1;
		bool structFlag = false;

		for (unsigned int k = 0; k < weightCount; k++)
		{
			MObjectArray	targetArray;

			int weightIndex = weightIndexArray[k];
			deformer->getTargets(node, weightIndex, targetArray);

			unsigned int targetCount = targetArray.length();
			for (unsigned int m = 0; m < targetCount; m++)
			{
				if (weightAnimated[k])
				{
					ExportAnimationTrack(*weightAnimCurve[k], (std::string("mw") += std::to_string(morphIndex)).c_str(), structFlag, envelope);
					structFlag = true;
				}

				morphIndex++;
			}
		}

		indentLevel--;
		IndentWrite("}\n");
	}

	for (unsigned int k = weightCount; k > 0; k--)
	{
		delete weightAnimCurve[k - 1];
	}

	delete[] weightAnimCurve;
}

void OpenGexExport::ExportNode(const MDagPath& dagPath, const MObject& parent)
{
	// This function exports a single node in the scene and includes its name,
	// object reference, material references (for geometries), and transform.
	// Subnodes are then exported recursively.

	MObject node = dagPath.node();

	const NodeReference *nodeRef = FindNode(node);
	if (nodeRef)
	{
		static const char *const structIdentifier[kNodeTypeCount] =
		{
			"Node $", "BoneNode $", "GeometryNode $", "LightNode $", "CameraNode $"
		};

		int type = nodeRef->nodeType;

		IndentWrite(structIdentifier[type], 0, true);
		Write(nodeRef->structName.c_str());

		IndentWrite("{\n", 0, true);
		indentLevel++;

		bool structFlag = false;

		MFnDagNode dagNode(node);

		// Export the node's name if it has one.

		MString string = dagNode.name();
		const char *name = string.asUTF8();
		if (name[0] != 0)
		{
			IndentWrite("Name {string {\"");
			Write(name);
			Write("\"}}\n");

			structFlag = true;
		}

		// Export the object reference and material references.

		if (type == kNodeTypeGeometry)
		{
			MObjectArray	shaderArray;
			MIntArray		shaderIndexArray;

			MObject baseObject = dagNode.child(nodeRef->childIndex);
			ObjectReference *objectRef = FindObject(geometryArray, baseObject);
			if (!objectRef)
			{
				int size = (int) geometryArray->size();
				geometryArray->push_back(ObjectReference(baseObject, (std::string("geometry") += std::to_string(size + 1)).c_str(), node));
				objectRef = &geometryArray->at(size);
			}
			else
			{
				objectRef->nodeTable.push_back(node);
			}

			IndentWrite("ObjectRef {ref {$");
			Write(objectRef->structName.c_str());
			Write("}}\n");

			MFnMesh mesh(baseObject);
			if (mesh.getConnectedShaders(dagPath.instanceNumber(), shaderArray, shaderIndexArray) == MStatus::kSuccess)
			{
				unsigned int shaderCount = shaderArray.length();
				for (unsigned int i = 0; i < shaderCount; i++)
				{
					ExportMaterialRef(shaderArray[i], i);
				}
			}

			MFnSkinCluster *skin = GetSkinCluster(baseObject);
			if (skin)
			{
				MObject		object;

				if (FindSkinClusterInputGeometry(skin, &object))
				{
					baseObject = object;
				}
			}

			MFnBlendShapeDeformer *deformer = GetBlendShapeDeformer(baseObject);
			if (deformer)
			{
				ExportMorphWeights(baseObject, deformer);
			}

			structFlag = true;
		}
		else if (type == kNodeTypeLight)
		{
			MObject object = dagNode.child(nodeRef->childIndex);
			ObjectReference *objectRef = FindObject(lightArray, object);
			if (!objectRef)
			{
				int size = (int) lightArray->size();
				lightArray->push_back(ObjectReference(object, (std::string("light") += std::to_string(size + 1)).c_str(), node));
				objectRef = &lightArray->at(size);
			}
			else
			{
				objectRef->nodeTable.push_back(node);
			}

			IndentWrite("ObjectRef {ref {$");
			Write(objectRef->structName.c_str());
			Write("}}\n");

			structFlag = true;
		}
		else if (type == kNodeTypeCamera)
		{
			MObject object = dagNode.child(nodeRef->childIndex);
			ObjectReference *objectRef = FindObject(cameraArray, object);
			if (!objectRef)
			{
				int size = (int) cameraArray->size();
				cameraArray->push_back(ObjectReference(object, (std::string("camera") += std::to_string(size + 1)).c_str(), node));
				objectRef = &cameraArray->at(size);
			}
			else
			{
				objectRef->nodeTable.push_back(node);
			}

			IndentWrite("ObjectRef {ref {$");
			Write(objectRef->structName.c_str());
			Write("}}\n");

			structFlag = true;
		}

		if (structFlag)
		{
			Write("\n");
		}

		// Export the transform. If the node is animated, then animation tracks are exported here.

		ExportTransform(node, parent);
	}

	// Recursively export the subnodes.

	unsigned int subnodeCount = dagPath.childCount();
	for (unsigned int i = 0; i < subnodeCount; i++)
	{
		MDagPath childPath(dagPath);
		childPath.push(dagPath.child(i));
		ExportNode(childPath, node);
	}

	if (nodeRef)
	{
		indentLevel--;
		IndentWrite("}\n");
	}
}

void OpenGexExport::ExportSkin(const MFnSkinCluster& skin, const MObject& object, int vertexCount, const OpenGex::ExportVertex *exportVertex)
{
	// This function exports all skinning data, which includes the skeleton
	// and per-vertex bone influence data.

	MDagPathArray	dagPathArray;
	MObject			matrixObject;

	IndentWrite("Skin\n", 0, true);
	IndentWrite("{\n");
	indentLevel++;

	// Write the skin bind pose transform.

	IndentWrite("Transform\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[16]\n");
	IndentWrite("{\n");

	skin.findPlug("geomMatrix", true).getValue(matrixObject);
	WriteMatrix(MFnMatrixData(matrixObject).matrix());
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n\n");

	// Export the skeleton, which includes an array of bone node references
	// and and array of per-bone bind pose transforms.

	IndentWrite("Skeleton\n");
	IndentWrite("{\n");
	indentLevel++;

	// Write the bone node reference array.

	IndentWrite("BoneRefArray\n");
	IndentWrite("{\n");
	indentLevel++;

	unsigned int boneCount = skin.influenceObjects(dagPathArray);
	const MDagPath **boneTable = new const MDagPath *[boneCount];
	unsigned int *boneIndexTable = new unsigned int[boneCount];
	for (unsigned int i = 0; i < boneCount; i++)
	{
		boneTable[i] = nullptr;
		boneIndexTable[i] = 0;
	}

	unsigned int maxBoneIndex = 0;
	for (unsigned int i = 0; i < boneCount; i++)
	{
		unsigned int k = skin.indexForInfluenceObject(dagPathArray[i]);
		boneIndexTable[i] = k;

		if (k > maxBoneIndex)
		{
			maxBoneIndex = k;
		}
	}

	unsigned int *inverseBoneIndexTable = new unsigned int[maxBoneIndex + 1];
	for (unsigned int i = 0; i <= maxBoneIndex; i++)
	{
		inverseBoneIndexTable[i] = 0;
	}

	for (unsigned int i = 0; i < boneCount; i++)
	{
		const MDagPath& dagPath = dagPathArray[i];
		inverseBoneIndexTable[skin.indexForInfluenceObject(dagPath)] = i;
		boneTable[i] = &dagPath;
	}

	IndentWrite("ref\t\t\t// ");
	WriteInt(boneCount);
	IndentWrite("{\n", 0, true);
	IndentWrite("", 1);

	for (unsigned int i = 0; i < boneCount; i++)
	{
		const NodeReference *boneRef = nullptr;

		const MDagPath *bone = boneTable[i];
		if (bone)
		{
			boneRef = FindNode(bone->node());
		}

		if (boneRef)
		{
			Write("$");
			Write(boneRef->structName.c_str());
		}
		else
		{
			Write("null");
		}

		if (i < boneCount - 1)
		{
			Write(", ");
		}
		else
		{
			Write("\n");
		}
	}

	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n\n");

	// Write the bind pose transform array.

	MPlug bindMatrixPlug = skin.findPlug("bindPreMatrix", true);

	IndentWrite("Transform\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[16]\t// ");
	WriteInt(boneCount);
	IndentWrite("{\n", 0, true);

	for (unsigned int i = 0; i < boneCount; i++)
	{
		bindMatrixPlug.elementByLogicalIndex(boneIndexTable[i]).getValue(matrixObject);
		WriteHexMatrixFlat(MFnMatrixData(matrixObject).matrix().inverse());

		if (i < boneCount - 1)
		{
			Write(",\n");
		}
	}

	IndentWrite("}\n", 0, true);

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n\n");

	// Export the per-vertex bone influence data.

	MPlug weightPlug = skin.findPlug("weightList", true);
	MObject weightAttrib = skin.attribute("weights");

	int weightCount = 0;
	int *countArray = new int[vertexCount];

	for (int i = 0; i < vertexCount; i++)
	{
		MPlug vertexPlug = weightPlug.elementByPhysicalIndex(exportVertex[i].vertexIndex);

		int count = vertexPlug.child(weightAttrib).numElements();
		countArray[i] = count;
		weightCount += count;
	}

	// Write the bone count array. There is one entry per vertex.

	IndentWrite("BoneCountArray\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("uint16\t\t// ");
	WriteInt(vertexCount);
	IndentWrite("{\n", 0, true);
	WriteIntArray(vertexCount, countArray);
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n\n");

	// Write the bone index array. The number of entries is the sum of the
	// bone counts for all vertices.

	IndentWrite("BoneIndexArray\n");
	IndentWrite("{\n");
	indentLevel++;

	int *indexArray = new int[weightCount];
	int *index = indexArray;
	for (int i = 0; i < vertexCount; i++)
	{
		MIntArray	influenceArray;

		MPlug vertexPlug = weightPlug.elementByPhysicalIndex(exportVertex[i].vertexIndex);

		int count = vertexPlug.child(weightAttrib).getExistingArrayAttributeIndices(influenceArray);
		for (int j = 0; j < count; j++)
		{
			index[j] = inverseBoneIndexTable[influenceArray[j]];
		}

		index += count;
	}

	IndentWrite("uint16\t\t// ");
	WriteInt(weightCount);
	IndentWrite("{\n", 0, true);
	WriteIntArray(weightCount, indexArray);
	IndentWrite("}\n");

	delete[] indexArray;

	indentLevel--;
	IndentWrite("}\n\n");

	// Write the bone weight array. The number of entries is the sum of the
	// bone counts for all vertices.

	IndentWrite("BoneWeightArray\n");
	IndentWrite("{\n");
	indentLevel++;

	float *weightArray = new float[weightCount];
	float *weight = weightArray;
	for (int i = 0; i < vertexCount; i++)
	{
		MIntArray	influenceArray;

		MPlug vertexPlug = weightPlug.elementByPhysicalIndex(exportVertex[i].vertexIndex);
		MPlug weightPlug = vertexPlug.child(weightAttrib);

		int count = weightPlug.getExistingArrayAttributeIndices(influenceArray);
		for (int j = 0; j < count; j++)
		{
			weightPlug.elementByLogicalIndex(influenceArray[j]).getValue(weight[j]);
		}

		weight += count;
	}

	IndentWrite("float\t\t// ");
	WriteInt(weightCount);
	IndentWrite("{\n", 0, true);
	WriteFloatArray(weightCount, weightArray);
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n");

	delete[] weightArray;
	delete[] countArray;

	delete[] inverseBoneIndexTable;
	delete[] boneIndexTable;
	delete[] boneTable;

	indentLevel--;
	IndentWrite("}\n");
}

void OpenGexExport::ExportGeometry(const OpenGex::ObjectReference *objectRef)
{
	// This function exports a single geometry object.

	MStatus			status;
	MObjectArray	shaderArray;
	MIntArray		shaderIndexArray;
	MIntArray		weightIndexArray;
	unsigned int	geometryIndex;
	int				triangleCount, colorCount, texcoordCount;
	int				*polygonIndexArray;

	MObject baseObject = objectRef->object;
	MFnMesh *mesh = new MFnMesh(baseObject);

	Write("\nGeometryObject $");
	Write(objectRef->structName.c_str());

	bool visibleFlag = true;
	bool shadowFlag = true;
	bool motionBlurFlag = true;

	MPlug visiblePlug = mesh->findPlug("primaryVisibility", false, &status);
	if (status == MS::kSuccess)
	{
		visiblePlug.getValue(visibleFlag);
	}

	MPlug shadowPlug = mesh->findPlug("castsShadows", false, &status);
	if (status == MS::kSuccess)
	{
		shadowPlug.getValue(shadowFlag);
	}

	MPlug motionBlurPlug = mesh->findPlug("motionBlur", false, &status);
	if (status == MS::kSuccess)
	{
		motionBlurPlug.getValue(motionBlurFlag);
	}

	if ((!visibleFlag) || (!shadowFlag) || (!motionBlurFlag))
	{
		Write(" (");
		bool propertyFlag = false;

		if (!visibleFlag)
		{
			Write("visible = false");
			propertyFlag = true;
		}

		if (!shadowFlag)
		{
			if (propertyFlag)
			{
				Write(", shadow = false");
			}
			else
			{
				Write("shadow = false");
				propertyFlag = true;
			}
		}

		if (!motionBlurFlag)
		{
			if (propertyFlag)
			{
				Write(", motion_blur = false");
			}
			else
			{
				Write("motion_blur = false");
				propertyFlag = true;
			}
		}

		Write(")");
	}

	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	MFnSkinCluster *skin = GetSkinCluster(baseObject);
	if (skin)
	{
		MObject		object;

		// Get the object containing the vertex positions before they are deformed
		// by the skin cluster. We need this in order to export the proper bind pose.

		if (FindSkinClusterInputGeometry(skin, &object))
		{
			baseObject = object;
		}
	}

	bool structFlag = false;

	MFnBlendShapeDeformer *deformer = GetBlendShapeDeformer(baseObject, &geometryIndex);
	if (deformer)
	{
		MObject		object;

		// Get the object containing the vertex positions before they are deformed by
		// the blend shape deformer. We need this in order to export the proper base mesh.

		if (FindBlendShapeDeformerInputGeometry(deformer, geometryIndex, &object))
		{
			baseObject = object;
		}

		deformer->weightIndexList(weightIndexArray);

		int morphIndex = 1;
		unsigned int weightCount = weightIndexArray.length();
		for (unsigned int k = 0; k < weightCount; k++)
		{
			MObjectArray	targetArray;

			int weightIndex = weightIndexArray[k];
			deformer->getTargets(objectRef->object, weightIndex, targetArray);

			unsigned int targetCount = targetArray.length();
			for (unsigned int m = 0; m < targetCount; m++)
			{
				IndentWrite("Morph (index = ", 0, structFlag);
				WriteInt(morphIndex);
				Write(", base = 0)\n");
				IndentWrite("{\n");
				IndentWrite("Name {string {\"", 1);
				Write(MFnDependencyNode(targetArray[m]).name().asChar());
				Write("\"}}\n");
				IndentWrite("}\n");

				structFlag = true;
				morphIndex++;
			}
		}
	}

	MFnMesh *baseMesh = new MFnMesh(baseObject);
	if (baseMesh->numVertices() != mesh->numVertices())
	{
		delete baseMesh;
		baseMesh = mesh;
	}

	bool opposite = false;
	MPlug oppositePlug = mesh->findPlug("opposite", false, &status);
	if (status == MS::kSuccess)
	{
		oppositePlug.getValue(opposite);
	}

	IndentWrite("Mesh (primitive = \"triangles\")\n", 0, structFlag);
	IndentWrite("{\n");
	indentLevel++;

	ExportVertex *exportVertex = DeindexMesh(mesh, baseMesh, &triangleCount, &colorCount, &texcoordCount, &polygonIndexArray);
	ExportVertex *unifiedVertex = new ExportVertex[triangleCount * 3];
	int *indexTable = new int[triangleCount * 3];
	int unifiedCount = UnifyVertices(triangleCount * 3, exportVertex, unifiedVertex, indexTable);

	if (opposite)
	{
		for (int i = 0; i < unifiedCount; i++)
		{
			unifiedVertex[i].normal = -unifiedVertex[i].normal;
		}
	}

	// Write the position array.

	IndentWrite("VertexArray (attrib = \"position\")\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[3]\t\t// ");
	WriteInt(unifiedCount);
	IndentWrite("{\n", 0, true);
	WriteVertexArray(unifiedCount, &unifiedVertex->position, sizeof(ExportVertex));
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n\n");

	// Write the normal array.

	IndentWrite("VertexArray (attrib = \"normal\")\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[3]\t\t// ");
	WriteInt(unifiedCount);
	IndentWrite("{\n", 0, true);
	WriteVertexArray(unifiedCount, &unifiedVertex->normal, sizeof(ExportVertex));
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n");

	// Write the color arrays.

	for (int k = 0; k < colorCount; k++)
	{
		IndentWrite("VertexArray (attrib = \"color\"", 0, true);

		if (k != 0)
		{
			Write(", index = ");
			WriteInt(k);
		}

		Write(")\n");

		IndentWrite("{\n");
		indentLevel++;

		IndentWrite("float[3]\t\t// ");
		WriteInt(unifiedCount);
		IndentWrite("{\n", 0, true);
		WriteVertexArray(unifiedCount, &unifiedVertex->color[k], sizeof(ExportVertex));
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");
	}

	// Write the texcoord arrays.

	for (int k = 0; k < texcoordCount; k++)
	{
		IndentWrite("VertexArray (attrib = \"texcoord\"", 0, true);

		if (k != 0)
		{
			Write(", index = ");
			WriteInt(k);
		}

		Write(")\n");

		IndentWrite("{\n");
		indentLevel++;

		IndentWrite("float[2]\t\t// ");
		WriteInt(unifiedCount);
		IndentWrite("{\n", 0, true);
		WriteVertexArray(unifiedCount, &unifiedVertex->texcoord[k], sizeof(ExportVertex));
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");
	}

	// If there are multiple morph targets, export them here.

	if (deformer)
	{
		int morphIndex = 1;
		unsigned int weightCount = weightIndexArray.length();
		for (unsigned int k = 0; k < weightCount; k++)
		{
			MObjectArray	targetArray;

			int weightIndex = weightIndexArray[k];
			deformer->getTargets(objectRef->object, weightIndex, targetArray);

			unsigned int targetCount = targetArray.length();
			for (unsigned int m = 0; m < targetCount; m++)
			{
				const MObject& target = targetArray[m];
				if (target.hasFn(MFn::kMesh))
				{
					MFloatPointArray	morphVertexArray;
					MFloatVectorArray	morphNormalArray;

					MFnMesh targetMesh(target);
					targetMesh.getPoints(morphVertexArray);
					targetMesh.getNormals(morphNormalArray);

					if ((morphVertexArray.length() == baseMesh->numVertices()) && (morphNormalArray.length() == baseMesh->numNormals()))
					{
						// Write the morph target position array.

						IndentWrite("VertexArray (attrib = \"position\", morph = ", 0, true);
						WriteInt(morphIndex);
						Write(")\n");
						IndentWrite("{\n");
						indentLevel++;

						IndentWrite("float[3]\t\t// ");
						WriteInt(unifiedCount);
						IndentWrite("{\n", 0, true);
						WriteMorphVertexArray(unifiedCount, unifiedVertex, morphVertexArray);
						IndentWrite("}\n");

						indentLevel--;
						IndentWrite("}\n");

						// Write the morph target normal array.

						IndentWrite("VertexArray (attrib = \"normal\", morph = ", 0, true);
						WriteInt(morphIndex);
						Write(")\n");
						IndentWrite("{\n");
						indentLevel++;

						IndentWrite("float[3]\t\t// ");
						WriteInt(unifiedCount);
						IndentWrite("{\n", 0, true);
						WriteMorphNormalArray(unifiedCount, unifiedVertex, morphNormalArray);
						IndentWrite("}\n");

						indentLevel--;
						IndentWrite("}\n");
					}
				}

				morphIndex++;
			}
		}
	}

	// Write the index arrays.

	int maxShaderIndex = 0;
	bool unassignedShader = false;

	if (mesh->getConnectedShaders(0, shaderArray, shaderIndexArray) == MStatus::kSuccess)
	{
		unsigned int polygonCount = shaderIndexArray.length();
		for (unsigned int i = 0; i < polygonCount; i++)
		{
			int index = shaderIndexArray[i];
			if (index > maxShaderIndex)
			{
				maxShaderIndex = index;
			}
			else if (index < 0)
			{
				unassignedShader = true;
			}
		}
	}

	if ((maxShaderIndex == 0) && (!unassignedShader))
	{
		// There is only one material, so write a single index array.

		IndentWrite((opposite) ? "IndexArray (front = \"cw\")\n" : "IndexArray\n", 0, true);
		IndentWrite("{\n");
		indentLevel++;

		IndentWrite("uint32[3]\t\t// ");
		WriteInt(triangleCount);
		IndentWrite("{\n", 0, true);
		WriteTriangleArray(triangleCount, indexTable);
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");
	}
	else
	{
		// If there are multiple shaders, then write a separate
		// index array for each one.

		int materialCount = maxShaderIndex + 2;
		int *materialTriangleCount = new int[materialCount];
		memset(materialTriangleCount, 0, materialCount * sizeof(int));

		for (int i = 0; i < triangleCount; i++)
		{
			int index = shaderIndexArray[polygonIndexArray[i]];
			if (index < 0)
			{
				index = maxShaderIndex + 1;
			}

			materialTriangleCount[index]++;
		}

		int *materialIndexTable = new int[triangleCount * 3];

		for (int m = 0; m < materialCount; m++)
		{
			if (materialTriangleCount[m] != 0)
			{
				int materialIndexCount = 0;
				for (int i = 0; i < triangleCount; i++)
				{
					int index = shaderIndexArray[polygonIndexArray[i]];
					if (index < 0)
					{
						index = maxShaderIndex + 1;
					}

					if (index == m)
					{
						int k = i * 3;
						materialIndexTable[materialIndexCount] = indexTable[k];
						materialIndexTable[materialIndexCount + 1] = indexTable[k + 1];
						materialIndexTable[materialIndexCount + 2] = indexTable[k + 2];
						materialIndexCount += 3;
					}
				}

				IndentWrite("IndexArray (material = ", 0, true);
				WriteInt((int) m);
				Write(")\n");
				IndentWrite("{\n");
				indentLevel++;

				IndentWrite("uint32[3]\t\t// ");
				WriteInt(materialTriangleCount[m]);
				IndentWrite("{\n", 0, true);
				WriteTriangleArray(materialTriangleCount[m], materialIndexTable);
				IndentWrite("}\n");

				indentLevel--;
				IndentWrite("}\n");
			}
		}

		delete[] materialIndexTable;
		delete[] materialTriangleCount;
	}

	// If the mesh is skinned, export the skinning data here.

	if (skin)
	{
		ExportSkin(*skin, objectRef->object, unifiedCount, unifiedVertex);
	}

	// Clean up.

	delete[] indexTable;
	delete[] unifiedVertex;
	delete[] polygonIndexArray;
	delete[] exportVertex;

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	Write("}\n");

	if (baseMesh != mesh)
	{
		delete baseMesh;
	}

	delete deformer;
	delete skin;
	delete mesh;
}

void OpenGexExport::ExportLight(const OpenGex::ObjectReference *objectRef)
{
	// This function exports a single light object.

	Write("\nLightObject $");
	Write(objectRef->structName.c_str());

	const MObject& object = objectRef->object;

	Write(" (type = ");
	bool pointFlag = false;
	bool spotFlag = false;

	if (object.hasFn(MFn::kSpotLight))
	{
		Write("\"spot\"");
		pointFlag = true;
		spotFlag = true;
	}
	else if (object.hasFn(MFn::kPointLight))
	{
		Write("\"point\"");
		pointFlag = true;
	}
	else
	{
		Write("\"infinite\"");
	}

	MFnNonExtendedLight light(object);

	if (!light.useDepthMapShadows())
	{
		Write(", shadow = false");
	}

	Write(")");
	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	// Export the light's color, and include a separate intensity if necessary.

	IndentWrite("Color (attrib = \"light\") {float[3] {");
	WriteColor(light.color());
	Write("}}\n");

	float intensity = light.intensity();
	if (intensity != 1.0F)
	{
		IndentWrite("Param (attrib = \"intensity\") {float {");
		WriteFloat(intensity);
		Write("}}\n");
	}

	if (pointFlag)
	{
		// Export an attenuation function.

		int decay = light.decayRate();
		if (decay != 0)
		{
			IndentWrite("Atten (curve = \"", 0, true);
			Write((decay == 1) ? "inverse\")\n" : "inverse_square\")\n");
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"scale\") {float {", 1);
			WriteFloat(1.0F);
			Write("}}\n");

			IndentWrite("}\n");
		}

		if (spotFlag)
		{
			// Export additional angular attenuation for spot lights.

			MFnSpotLight spot(object);

			IndentWrite("Atten (kind = \"cos_angle\", curve = \"linear\")\n", 0, true);
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"begin\") {float {", 1);
			WriteFloat(0.0F);
			Write("}}\n");

			IndentWrite("Param (attrib = \"end\") {float {", 1);
			WriteFloat(cos(float(spot.coneAngle()) * 0.5F));
			Write("}}\n");

			IndentWrite("Param (attrib = \"power\") {float {", 1);
			WriteFloat(float(spot.dropOff()));
			Write("}}\n");

			IndentWrite("}\n");
		}
	}

	indentLevel--;
	Write("}\n");
}

void OpenGexExport::ExportCamera(const OpenGex::ObjectReference *objectRef)
{
	// This function exports a single camera object.

	Write("\nCameraObject $");
	Write(objectRef->structName.c_str());
	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	MFnCamera camera(objectRef->object);

	IndentWrite("Param (attrib = \"fov\") {float {");
	WriteFloat(float(camera.horizontalFieldOfView()));
	Write("}}\n");

	IndentWrite("Param (attrib = \"near\") {float {");
	WriteFloat(float(camera.nearClippingPlane()));
	Write("}}\n");

	IndentWrite("Param (attrib = \"far\") {float {");
	WriteFloat(float(camera.farClippingPlane()));
	Write("}}\n");

	indentLevel--;
	Write("}\n");
}

void OpenGexExport::ExportObjects(void)
{
	int count = (int) geometryArray->size();
	if (count != 0)
	{
		const ObjectReference *objectRef = &geometryArray->front();
		for (int i = 0; i < count; i++)
		{
			ExportGeometry(objectRef);
			objectRef++;
		}
	}

	count = (int) lightArray->size();
	if (count != 0)
	{
		const ObjectReference *objectRef = &lightArray->front();
		for (int i = 0; i < count; i++)
		{
			ExportLight(objectRef);
			objectRef++;
		}
	}

	count = (int) cameraArray->size();
	if (count != 0)
	{
		const ObjectReference *objectRef = &cameraArray->front();
		for (int i = 0; i < count; i++)
		{
			ExportCamera(objectRef);
			objectRef++;
		}
	}
}

bool OpenGexExport::ExportTexture(const MFnDependencyNode& shader, const char *input, const char *attrib)
{
	MStatus		status;

	MPlug plug = shader.findPlug(input, false, &status);
	if (status == MStatus::kSuccess)
	{
		MPlugArray	plugArray;

		if ((plug.connectedTo(plugArray, true, false)) && (plugArray.length() != 0))
		{
			MObject object = plugArray[0].node();

			if (object.apiType() == MFn::kBump)
			{
				plug = MFnDependencyNode(object).findPlug("bumpValue", false, &status);
				if (status == MStatus::kSuccess)
				{
					if ((plug.connectedTo(plugArray, true, false)) && (plugArray.length() != 0))
					{
						object = plugArray[0].node();
					}
				}
			}

			if (object.apiType() == MFn::kFileTexture)
			{
				MFnDependencyNode texture(object);

				MPlug filePlug = texture.findPlug("fileTextureName", false, &status);
				if (status == MStatus::kSuccess)
				{
					MString name = filePlug.asString();

					IndentWrite("Texture (attrib = \"", 0, true);
					Write(attrib);
					Write("\"");

					const TextureReference *textureRef = FindTexture(object);
					if (textureRef)
					{
						Write(", texcoord = ");
						WriteInt(textureRef->texcoord);
					}

					Write(")\n");
					IndentWrite("{\n");
					indentLevel++;

					IndentWrite("string {\"");
					WriteFileName(name.asChar());
					Write("\"}\n");

					// If the texture has a scale and/or offset, then export a coordinate transform.

					MPlug uvPlug = texture.findPlug("uvCoord", false, &status);
					if (status == MStatus::kSuccess)
					{
						if ((uvPlug.connectedTo(plugArray, true, false)) && (plugArray.length() != 0))
						{
							MObject uvObject = plugArray[0].node();
							if (uvObject.hasFn(MFn::kPlace2dTexture))
							{
								MFnDependencyNode place(uvObject);

								float uscale = place.findPlug("repeatU", false).asFloat();
								float vscale = place.findPlug("repeatV", false).asFloat();
								float uoffset = place.findPlug("offsetU", false).asFloat();
								float voffset = place.findPlug("offsetV", false).asFloat();

								if ((uscale != 1.0F) || (vscale != 1.0F) || (uoffset != 0.0F) || (voffset != 0.0F))
								{
									MMatrix		matrix;

									matrix.setToIdentity();
									matrix(0,0) = uscale;
									matrix(1,1) = vscale;
									matrix(3,0) = uoffset;
									matrix(3,1) = voffset;

									IndentWrite("Transform\n", 0, true);
									IndentWrite("{\n");
									indentLevel++;

									IndentWrite("float[16]\n");
									IndentWrite("{\n");
									WriteMatrix(matrix);
									IndentWrite("}\n");

									indentLevel--;
									IndentWrite("}\n");
								}
							}
						}
					}

					indentLevel--;
					IndentWrite("}\n");

					return (true);
				}
			}
		}
	}

	return (false);
}

void OpenGexExport::ExportMaterials(void)
{
	// This function exports all of the materials used in the scene.

	int count = (int) materialArray->size();
	if (count != 0)
	{
		const MaterialReference *materialRef = &materialArray->front();
		for (int i = 0; i < count; i++)
		{
			MStatus		status;

			Write("\nMaterial $");
			Write(materialRef->structName.c_str());

			Write("\n{\n");
			indentLevel++;

			MFnDependencyNode material(materialRef->material);

			MPlug shaderPlug = material.findPlug("surfaceShader", false, &status);
			if (status == MStatus::kSuccess)
			{
				MPlugArray	plugArray;

				if ((shaderPlug.connectedTo(plugArray, true, false)) && (plugArray.length() != 0))
				{
					MObject surfaceShader = plugArray[0].node();
					MFnDependencyNode shader(surfaceShader);

					IndentWrite("Name {string {\"");
					Write(shader.name().asUTF8());
					Write("\"}}\n");

					bool diffuseTexture = ExportTexture(shader, "color", "diffuse");
					bool specularTexture = ExportTexture(shader, "specularColor", "specular");
					bool emissionTexture = ExportTexture(shader, "incandescence", "emission");
					bool transparencyTexture = ExportTexture(shader, "transparency", "transparency");
					ExportTexture(shader, "normalCamera", "normal");

					if (surfaceShader.hasFn(MFn::kLambert))
					{
						MFnLambertShader lambert(surfaceShader);
						float diffuse = lambert.diffuseCoeff();

						IndentWrite("Color (attrib = \"diffuse\") {float[3] {", 0, true);
						if (diffuseTexture)
						{
							WriteColor(MColor(diffuse, diffuse, diffuse));
						}
						else
						{
							WriteColor(lambert.color() * diffuse);
						}

						Write("}}\n");

						if (surfaceShader.hasFn(MFn::kPhong))
						{
							MFnPhongShader phong(surfaceShader);

							bool powerFlag = specularTexture;
							if (!specularTexture)
							{
								MColor specular = phong.specularColor();
								if ((specular.r > 0.0F) || (specular.g > 0.0F) || (specular.b > 0.0F))
								{
									IndentWrite("Color (attrib = \"specular\") {float[3] {");
									WriteColor(specular);
									Write("}}\n");

									powerFlag = true;
								}
							}

							if (powerFlag)
							{
								IndentWrite("Param (attrib = \"specular_power\") {float {");
								WriteFloat(phong.cosPower());
								Write("}}\n");
							}
						}

						if (!emissionTexture)
						{
							MColor emission = lambert.incandescence();
							if ((emission.r > 0.0F) || (emission.g > 0.0F) || (emission.b > 0.0F))
							{
								IndentWrite("Color (attrib = \"emission\") {float[3] {");
								WriteColor(emission);
								Write("}}\n");
							}
						}

						if (!transparencyTexture)
						{
							MColor transparency = lambert.transparency();
							if ((transparency.r > 0.0F) || (transparency.g > 0.0F) || (transparency.b > 0.0F))
							{
								IndentWrite("Color (attrib = \"transparency\") {float[3] {");
								WriteColor(transparency);
								Write("}}\n");
							}
						}
					}
				}
			}

			indentLevel--;
			Write("}\n");

			materialRef++;
		}
	}
}

void OpenGexExport::ExportMetrics(void)
{
	Write("Metric (key = \"distance\") {float {0.01}}\n");
	Write("Metric (key = \"angle\") {float {1}}\n");
	Write("Metric (key = \"time\") {float {1}}\n");

	Write("Metric (key = \"up\") {string {\"");
	Write(MGlobal::isZAxisUp() ? "z" : "y");
	Write("\"}}\n");
}


__declspec(dllexport) MStatus initializePlugin(MObject object)
{
	MStatus status = MS::kSuccess;
	MFnPlugin plugin(object, "Terathon Software OpenGEX Exporter", "3.0", "Any", &status);

	if (status == MS::kSuccess)
	{
		status = plugin.registerFileTranslator("OpenGEX", "", &OpenGexExport::New);
	}

	return (status);
}

__declspec(dllexport) MStatus uninitializePlugin(MObject object)
{
	MFnPlugin plugin(object);
	return (plugin.deregisterFileTranslator("OpenGEX"));
}
