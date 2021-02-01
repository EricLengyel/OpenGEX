//
// OpenGEX exporter for 3ds Max
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


#include "OpenGex-Max.h"


namespace
{
	OpenGexClassDesc	TheClassDesc;


	const float kDegToRad = 0.01745329252F;		// pi / 180
	const float kExportEpsilon = 1.0e-6F;		// Values smaller than this are considered to be zero.


	// The following functions determine whether two animation keys have values that are close
	// enough to be considered equal. An animation track is not exported when all of the keys
	// in the track have the same value.

	template <class keyType> inline bool KeysEqual(const keyType& key1, const keyType& key2)
	{
		return (fabs(key1.val - key2.val) < kExportEpsilon);
	}

	inline bool KeysEqual(const ILinPoint3Key& key1, const ILinPoint3Key& key2)
	{
		return ((fabs(key1.val.x - key2.val.x) < kExportEpsilon) && (fabs(key1.val.y - key2.val.y) < kExportEpsilon) && (fabs(key1.val.z - key2.val.z) < kExportEpsilon));
	}

	inline bool KeysEqual(const IBezPoint3Key& key1, const IBezPoint3Key& key2)
	{
		return ((fabs(key1.val.x - key2.val.x) < kExportEpsilon) && (fabs(key1.val.y - key2.val.y) < kExportEpsilon) && (fabs(key1.val.z - key2.val.z) < kExportEpsilon));
	}

	inline bool KeysEqual(const ITCBPoint3Key& key1, const ITCBPoint3Key& key2)
	{
		return ((fabs(key1.val.x - key2.val.x) < kExportEpsilon) && (fabs(key1.val.y - key2.val.y) < kExportEpsilon) && (fabs(key1.val.z - key2.val.z) < kExportEpsilon));
	}

	inline bool KeysEqual(const ILinRotKey& key1, const ILinRotKey& key2)
	{
		return ((fabs(key1.val.x - key2.val.x) < kExportEpsilon) && (fabs(key1.val.y - key2.val.y) < kExportEpsilon) && (fabs(key1.val.z - key2.val.z) < kExportEpsilon) && (fabs(key1.val.w - key2.val.w) < kExportEpsilon));
	}

	inline bool KeysEqual(const IBezQuatKey& key1, const IBezQuatKey& key2)
	{
		return ((fabs(key1.val.x - key2.val.x) < kExportEpsilon) && (fabs(key1.val.y - key2.val.y) < kExportEpsilon) && (fabs(key1.val.z - key2.val.z) < kExportEpsilon) && (fabs(key1.val.w - key2.val.w) < kExportEpsilon));
	}

	inline bool KeysEqual(const ITCBRotKey& key1, const ITCBRotKey& key2)
	{
		return ((fabs(key1.val.axis.x - key2.val.axis.x) < kExportEpsilon) && (fabs(key1.val.axis.y - key2.val.axis.y) < kExportEpsilon) && (fabs(key1.val.axis.z - key2.val.axis.z) < kExportEpsilon) && (fabs(key1.val.angle - key2.val.angle) < kExportEpsilon));
	}

	inline bool KeysEqual(const ILinScaleKey& key1, const ILinScaleKey& key2)
	{
		return ((fabs(key1.val.s.x - key2.val.s.x) < kExportEpsilon) && (fabs(key1.val.s.y - key2.val.s.y) < kExportEpsilon) && (fabs(key1.val.s.z - key2.val.s.z) < kExportEpsilon) && (fabs(key1.val.q.x - key2.val.q.x) < kExportEpsilon) && (fabs(key1.val.q.y - key2.val.q.y) < kExportEpsilon) && (fabs(key1.val.q.z - key2.val.q.z) < kExportEpsilon) && (fabs(key1.val.q.w - key2.val.q.w) < kExportEpsilon));
	}

	inline bool KeysEqual(const IBezScaleKey& key1, const IBezScaleKey& key2)
	{
		return ((fabs(key1.val.s.x - key2.val.s.x) < kExportEpsilon) && (fabs(key1.val.s.y - key2.val.s.y) < kExportEpsilon) && (fabs(key1.val.s.z - key2.val.s.z) < kExportEpsilon) && (fabs(key1.val.q.x - key2.val.q.x) < kExportEpsilon) && (fabs(key1.val.q.y - key2.val.q.y) < kExportEpsilon) && (fabs(key1.val.q.z - key2.val.q.z) < kExportEpsilon) && (fabs(key1.val.q.w - key2.val.q.w) < kExportEpsilon));
	}

	inline bool KeysEqual(const ITCBScaleKey& key1, const ITCBScaleKey& key2)
	{
		return ((fabs(key1.val.s.x - key2.val.s.x) < kExportEpsilon) && (fabs(key1.val.s.y - key2.val.s.y) < kExportEpsilon) && (fabs(key1.val.s.z - key2.val.s.z) < kExportEpsilon) && (fabs(key1.val.q.x - key2.val.q.x) < kExportEpsilon) && (fabs(key1.val.q.y - key2.val.q.y) < kExportEpsilon) && (fabs(key1.val.q.z - key2.val.q.z) < kExportEpsilon) && (fabs(key1.val.q.w - key2.val.q.w) < kExportEpsilon));
	}


	// The following functions determine whether the tangents for an animation key are small
	// enough to be considered zero. An animation track with Bezier keys is not exported when
	// all of the keys in the track have the same value and the tangents are all zero.

	template <class keyType> inline bool KeyTangentsNonzero(const keyType& key)
	{
		return ((fabs(key.intan) > kExportEpsilon) || (fabs(key.outtan) > kExportEpsilon));
	}

	inline bool KeyTangentsNonzero(const IBezPoint3Key& key)
	{
		return ((fabs(key.intan.x) > kExportEpsilon) || (fabs(key.intan.y) > kExportEpsilon) || (fabs(key.intan.z) > kExportEpsilon) || (fabs(key.outtan.x) > kExportEpsilon) || (fabs(key.outtan.y) > kExportEpsilon) || (fabs(key.outtan.z) > kExportEpsilon));
	}

	inline bool KeyTangentsNonzero(const IBezScaleKey& key)
	{
		return ((fabs(key.intan.x) > kExportEpsilon) || (fabs(key.intan.y) > kExportEpsilon) || (fabs(key.intan.z) > kExportEpsilon) || (fabs(key.outtan.x) > kExportEpsilon) || (fabs(key.outtan.y) > kExportEpsilon) || (fabs(key.outtan.z) > kExportEpsilon));
	}


	// The following functions are used for extracting values from the various animation
	// key types in a uniform way.

	template <class keyType> inline const Point3& GetKeyPoint3(const keyType& key)
	{
		return (key.val);
	}

	inline const Point3& GetKeyPoint3(const ILinScaleKey& key)
	{
		return (key.val.s);
	}

	inline const Point3& GetKeyPoint3(const IBezScaleKey& key)
	{
		return (key.val.s);
	}

	inline const Point3& GetKeyPoint3(const ITCBScaleKey& key)
	{
		return (key.val.s);
	}

	template <class keyType> inline const Quat& GetKeyQuat(const keyType& key)
	{
		return (key.val);
	}

	inline Quat GetKeyQuat(const ITCBRotKey& key)
	{
		return (QFromAngAxis(key.val.angle, key.val.axis));
	}

	inline const Quat& GetKeyQuat(const ILinScaleKey& key)
	{
		return (key.val.q);
	}

	inline const Quat& GetKeyQuat(const IBezScaleKey& key)
	{
		return (key.val.q);
	}

	inline const Quat& GetKeyQuat(const ITCBScaleKey& key)
	{
		return (key.val.q);
	}
}


using namespace MaxSDK;
using namespace OpenGex;


ExportVertex::ExportVertex()
{
	color.Set(1.0F, 1.0F, 1.0F);

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		texcoord[i].Set(0.0F, 0.0F);
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

	if (color != v.color)
	{
		return (false);
	}

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		if (texcoord[i] != v.texcoord[i])
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

	data = reinterpret_cast<const unsigned int *>(&color.x);

	h = ((h << 5) | (h >> 26)) + data[0];
	h = ((h << 5) | (h >> 26)) + data[1];
	h = ((h << 5) | (h >> 26)) + data[2];

	for (int i = 0; i < kMaxTexcoordCount; i++)
	{
		data = reinterpret_cast<const unsigned int *>(&texcoord[i].x);

		h = ((h << 5) | (h >> 26)) + data[0];
		h = ((h << 5) | (h >> 26)) + data[1];
	}

	hash = h;
}


OpenGexClassDesc::OpenGexClassDesc()
{
}

OpenGexClassDesc::~OpenGexClassDesc()
{
}

int OpenGexClassDesc::IsPublic(void)
{
	return (TRUE);
}

void *OpenGexClassDesc::Create(BOOL loading)
{
	return (new OpenGexExport);
}

const MCHAR *OpenGexClassDesc::ClassName(void)
{
	return (L"OpenGexExport");
}

SClass_ID OpenGexClassDesc::SuperClassID(void)
{
	return (SCENE_EXPORT_CLASS_ID);
}

Class_ID OpenGexClassDesc::ClassID(void)
{
	return (Class_ID(0x2EE12E7B, 0x2D6E34C3));
}

const MCHAR *OpenGexClassDesc::Category(void)
{
	return (L"");
}


OpenGexExport::OpenGexExport()
{
}

OpenGexExport::~OpenGexExport()
{
}

int OpenGexExport::ExtCount(void)
{
	return (1);
}

const MCHAR *OpenGexExport::Ext(int n)
{
	return (L"ogex");
}

const MCHAR *OpenGexExport::LongDesc(void)
{
	return (L"Open Game Engine Exchange File");
}

const MCHAR *OpenGexExport::ShortDesc(void)
{
	return (L"OpenGEX");
}

const MCHAR *OpenGexExport::AuthorName(void)
{
	return (L"Terathon Software");
}

const MCHAR *OpenGexExport::CopyrightMessage(void)
{
	return (L"Copyright 2013-2021");
}

const MCHAR *OpenGexExport::OtherMessage1(void)
{
	return (L"");
}

const MCHAR *OpenGexExport::OtherMessage2(void)
{
	return (L"");
}

unsigned int OpenGexExport::Version(void)
{
	return (300);
}

void OpenGexExport::ShowAbout(HWND hWnd)
{
}

int OpenGexExport::DoExport(const MCHAR *name, ExpInterface *ei, Interface *i, BOOL suppressPrompts, DWORD options)
{
	exportFile = CreateFileW(name, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
	if (exportFile == INVALID_HANDLE_VALUE)
	{
		return (IMPEXP_FAIL);
	}

	indentLevel = 0;

	ExportMetrics();

	Interval interval = i->GetAnimRange();
	startTime = interval.Start();
	endTime = interval.End();

	nodeArray = new std::vector<NodeReference>;
	geometryArray = new std::vector<ObjectReference>;
	lightArray = new std::vector<ObjectReference>;
	cameraArray = new std::vector<ObjectReference>;
	materialArray = new std::vector<MaterialReference>;

	bool exportAllFlag = ((options & SCENE_EXPORT_SELECTED) == 0);

	INode *root = i->GetRootNode();
	int nodeCount = root->NumberOfChildren();

	for (int i = 0; i < nodeCount; i++)
	{
		ProcessNode(root->GetChildNode(i), exportAllFlag);
	}

	ProcessSkinnedMeshes();

	for (int i = 0; i < nodeCount; i++)
	{
		ExportNode(root->GetChildNode(i));
	}

	ExportObjects();
	ExportMaterials();

	delete materialArray;
	delete cameraArray;
	delete lightArray;
	delete geometryArray;
	delete nodeArray;

	CloseHandle(exportFile);
	return (IMPEXP_SUCCESS);
}

BOOL OpenGexExport::SupportsOptions(int ext, DWORD options)
{
	if ((ext == 0) && (options == SCENE_EXPORT_SELECTED))
	{
		return (TRUE);
	}

	return (FALSE);
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

void OpenGexExport::WriteMatrix(const Matrix3& matrix) const
{
	const Point3 *row = &matrix[0];

	IndentWrite("{", 1);
	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000,\t\t// {");
	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0,\n");

	row = &matrix[1];

	IndentWrite(" ", 1);
	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000,\t\t//  ");
	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0,\n");

	row = &matrix[2];

	IndentWrite(" ", 1);
	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000,\t\t//  ");
	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0,\n");

	row = &matrix[3];

	IndentWrite(" ", 1);
	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x3F800000}\t\t//  ");
	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 1}\n");
}

void OpenGexExport::WriteMatrixFlat(const Matrix3& matrix) const
{
	const Point3 *row = &matrix[0];

	IndentWrite("{", 1);
	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0, ");

	row = &matrix[1];

	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0, ");

	row = &matrix[2];

	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 0, ");

	row = &matrix[3];

	WriteFloat(row->x);
	Write(", ");
	WriteFloat(row->y);
	Write(", ");
	WriteFloat(row->z);
	Write(", 1}");
}

void OpenGexExport::WriteHexMatrixFlat(const Matrix3& matrix) const
{
	const Point3 *row = &matrix[0];

	IndentWrite("{", 1);
	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000, ");

	row = &matrix[1];

	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000, ");

	row = &matrix[2];

	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x00000000, ");

	row = &matrix[3];

	WriteHexFloat(row->x);
	Write(", ");
	WriteHexFloat(row->y);
	Write(", ");
	WriteHexFloat(row->z);
	Write(", 0x3F800000}");
}

void OpenGexExport::WritePoint3(const Point3& point) const
{
	Write("{");
	WriteFloat(point.x);
	Write(", ");
	WriteFloat(point.y);
	Write(", ");
	WriteFloat(point.z);
	Write("}");
}

void OpenGexExport::WriteHexPoint3(const Point3& point) const
{
	Write("{");
	WriteHexFloat(point.x);
	Write(", ");
	WriteHexFloat(point.y);
	Write(", ");
	WriteHexFloat(point.z);
	Write("}");
}

void OpenGexExport::WriteQuat(const Quat& quat) const
{
	// Quaternions in Max rotate the wrong direction, so we have to negate the axis.

	Write("{");
	WriteFloat(-quat.x);
	Write(", ");
	WriteFloat(-quat.y);
	Write(", ");
	WriteFloat(-quat.z);
	Write(", ");
	WriteFloat(quat.w);
	Write("}");
}

void OpenGexExport::WriteHexQuat(const Quat& quat) const
{
	// Quaternions in Max rotate the wrong direction, so we have to negate the axis.

	Write("{");
	WriteHexFloat(-quat.x);
	Write(", ");
	WriteHexFloat(-quat.y);
	Write(", ");
	WriteHexFloat(-quat.z);
	Write(", ");
	WriteHexFloat(quat.w);
	Write("}");
}

void OpenGexExport::WriteColor(const Color& color) const
{
	Write("{");
	WriteFloat(color.r);
	Write(", ");
	WriteFloat(color.g);
	Write(", ");
	WriteFloat(color.b);
	Write("}");
}

void OpenGexExport::WriteFileName(const wchar_t *string) const
{
	const wchar_t *s = string;
	while (*s != 0)
	{
		s++;
	}

	if (s != string)
	{
		unsigned int length = (unsigned int) (s - string);
		wchar_t *buffer = new wchar_t[length + 3];

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
			wchar_t c = string[0];
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

void OpenGexExport::WriteVertex(const Point2& vertex) const
{
	Write("{");
	WriteHexFloat(vertex.x);
	Write(", ");
	WriteHexFloat(vertex.y);
	Write("}");
}

void OpenGexExport::WriteVertex(const Point3& vertex) const
{
	Write("{");
	WriteHexFloat(vertex.x);
	Write(", ");
	WriteHexFloat(vertex.y);
	Write(", ");
	WriteHexFloat(vertex.z);
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

void OpenGexExport::WriteMorphVertexArray(int count, const ExportVertex *exportVertex, const Point3 *morphVertex) const
{
	int lineCount = count >> 3;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 7; j++)
		{
			WriteVertex(morphVertex[exportVertex->index]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphVertex[exportVertex->index]);
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
			WriteVertex(morphVertex[exportVertex->index]);
			Write(", ");
			exportVertex++;
		}

		WriteVertex(morphVertex[exportVertex->index]);
		Write("\n");
	}
}

void OpenGexExport::WriteMorphNormalArray(int count, const Point3 *morphNormal) const
{
	int index = 0;

	int lineCount = count >> 3;
	for (int i = 0; i < lineCount; i++)
	{
		IndentWrite("", 1);
		for (int j = 0; j < 7; j++)
		{
			WriteVertex(morphNormal[index]);
			Write(", ");
			index++;
		}

		WriteVertex(morphNormal[index]);
		index++;

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
			WriteVertex(morphNormal[index]);
			Write(", ");
			index++;
		}

		WriteVertex(morphNormal[index]);
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
	INode *const *nodeTable = &objectRef->nodeTable.front();
	for (int k = 0; k < nodeCount; k++)
	{
		const MCHAR *name = nodeTable[k]->GetName();
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

int OpenGexExport::GetNodeType(INode *node) const
{
	// This function classifies a node based on its class ID and controller ID.

	Object *object = node->GetObjectRef();
	if (object)
	{
		object = object->Eval(startTime).obj;
		SClass_ID objectClass = object->SuperClassID();

		if (objectClass == GEOMOBJECT_CLASS_ID)
		{
			if (object->ClassID() == BONE_OBJ_CLASSID)
			{
				return (kNodeTypeBone);
			}

			Control *control = node->GetTMController();
			if (control)
			{
				Class_ID id = control->ClassID();
				if ((id == BIPSLAVE_CONTROL_CLASS_ID) || (id == BIPBODY_CONTROL_CLASS_ID))
				{
					return (kNodeTypeBone);
				}
			}

			if (object->CanConvertToType(Class_ID(TRIOBJ_CLASS_ID, 0)) != 0)
			{
				return (kNodeTypeGeometry);
			}
		}
		else if (objectClass == LIGHT_CLASS_ID)
		{
			ULONG classID = object->ClassID().PartA();
			if ((classID == OMNI_LIGHT_CLASS_ID) || (classID == SPOT_LIGHT_CLASS_ID) || (classID == DIR_LIGHT_CLASS_ID) || (classID == FSPOT_LIGHT_CLASS_ID) || (classID == TDIR_LIGHT_CLASS_ID))
			{
				return (kNodeTypeLight);
			}
		}
		else if (objectClass == CAMERA_CLASS_ID)
		{
			return (kNodeTypeCamera);
		}
	}

	return (kNodeTypeNode);
}

ISkin *OpenGexExport::GetSkinInterface(Object *object)
{
	// This function locates the skin interface for a geometry object if it has one.

	do
	{
		SClass_ID objectClass = object->SuperClassID();
		if ((objectClass != GEN_DERIVOB_CLASS_ID) && (objectClass != DERIVOB_CLASS_ID))
		{
			break;
		}

		IDerivedObject *derivedObject = static_cast<IDerivedObject *>(object);

		int modifierCount = derivedObject->NumModifiers();
		for (int i = 0; i < modifierCount; i++)
		{
			Modifier *modifier = derivedObject->GetModifier(i);
			if ((modifier->IsEnabled()) && (modifier->ClassID() == SKIN_CLASSID))
			{
				return (static_cast<ISkin *>(modifier->GetInterface(I_SKIN)));
			}
		}

		object = derivedObject->GetObjRef();
	} while (object);

	return (nullptr);
}

MorphR3 *OpenGexExport::GetMorphModifier(Object *object)
{
	// This function locates the morpher modifier for a geometry object if it has one.

	do
	{
		SClass_ID objectClass = object->SuperClassID();
		if ((objectClass != GEN_DERIVOB_CLASS_ID) && (objectClass != DERIVOB_CLASS_ID))
		{
			break;
		}

		IDerivedObject *derivedObject = static_cast<IDerivedObject *>(object);

		int modifierCount = derivedObject->NumModifiers();
		for (int i = 0; i < modifierCount; i++)
		{
			Modifier *modifier = derivedObject->GetModifier(i);
			if ((modifier->IsEnabled()) && (modifier->ClassID() == MR3_CLASS_ID))
			{
				MorphR3 *morpher = static_cast<MorphR3 *>(modifier);
				if (morpher->chanBank.size() != 0)
				{
					return (morpher);
				}
			}
		}

		object = derivedObject->GetObjRef();
	} while (object);

	return (nullptr);
}

bool OpenGexExport::ActiveMorphChannel(const morphChannel *channel)
{
	return ((channel->mActive) && (channel->mActiveOverride) && (!channel->mInvalid));
}

NodeReference *OpenGexExport::FindNode(const INode *node) const
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

ObjectReference *OpenGexExport::FindObject(std::vector<ObjectReference> *array, const Object *object)
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

MaterialReference *OpenGexExport::FindMaterial(const StdMat *material)
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

ExportVertex *OpenGexExport::DeindexMesh(Mesh *mesh, Mesh *baseMesh, int *exportTriangleCount, int *exportColorCount, int *exportTexcoordCount)
{
	// This function deindexes all vertex positions, colors, and texcoords.
	// Three separate ExportVertex structures are created for each triangle.

	int vertexCount = baseMesh->getNumVerts();
	const Point3 *vertex = baseMesh->getVertPtr(0);

	int triangleCount = mesh->getNumFaces();
	*exportTriangleCount = triangleCount;

	ExportVertex *exportVertex = new ExportVertex[triangleCount * 3];
	VertexNormal *vnormal = new VertexNormal[vertexCount];

	const Face *triangle = mesh->faces;
	for (int i = 0; i < triangleCount; i++)
	{
		int k1 = triangle[i].v[0];
		int k2 = triangle[i].v[1];
		int k3 = triangle[i].v[2];

		const Point3& v1 = vertex[k1];
		const Point3& v2 = vertex[k2];
		const Point3& v3 = vertex[k3];

		Point3 n = (v2 - v1) ^ (v3 - v1);
		DWORD smooth = triangle[i].smGroup;

		vnormal[k1].AddNormal(n, smooth);
		vnormal[k2].AddNormal(n, smooth);
		vnormal[k3].AddNormal(n, smooth);
	}

	ExportVertex *ev = exportVertex;
	for (int i = 0; i < triangleCount; i++)
	{
		unsigned int k1 = triangle[i].v[0];
		unsigned int k2 = triangle[i].v[1];
		unsigned int k3 = triangle[i].v[2];

		ev[0].index = k1;
		ev[1].index = k2;
		ev[2].index = k3;

		ev[0].position = vertex[k1];
		ev[1].position = vertex[k2];
		ev[2].position = vertex[k3];

		DWORD smooth = triangle[i].smGroup;
		ev[0].normal = Normalize(vnormal[k1].GetNormal(smooth));
		ev[1].normal = Normalize(vnormal[k2].GetNormal(smooth));
		ev[2].normal = Normalize(vnormal[k3].GetNormal(smooth));

		ev += 3;
	}

	delete[] vnormal;

	const VertColor *color = mesh->vertColArray;
	TVFace *colorFace = mesh->vcFaceData;
	if ((color) && (colorFace))
	{
		ev = exportVertex;
		for (int i = 0; i < triangleCount; i++)
		{
			unsigned int k1 = colorFace[i].t[0];
			unsigned int k2 = colorFace[i].t[1];
			unsigned int k3 = colorFace[i].t[2];

			ev[0].color = color[k1];
			ev[1].color = color[k2];
			ev[2].color = color[k3];

			ev += 3;
		}

		*exportColorCount = 1;
	}
	else
	{
		*exportColorCount = 0;
	}

	int texcoordCount = 0;
	int mapCount = mesh->getNumMaps();
	for (int m = 1; m < mapCount; m++)
	{
		if (mesh->mapSupport(m))
		{
			const MeshMap *map = &mesh->maps[m];
			const UVVert *texcoord = map->tv;
			const TVFace *texcoordFace = map->tf;

			ev = exportVertex;
			for (int i = 0; i < triangleCount; i++)
			{
				unsigned int k1 = texcoordFace[i].t[0];
				unsigned int k2 = texcoordFace[i].t[1];
				unsigned int k3 = texcoordFace[i].t[2];

				ev[0].texcoord[texcoordCount].Set(texcoord[k1].x, texcoord[k1].y);
				ev[1].texcoord[texcoordCount].Set(texcoord[k2].x, texcoord[k2].y);
				ev[2].texcoord[texcoordCount].Set(texcoord[k3].x, texcoord[k3].y);

				ev += 3;
			}

			if (++texcoordCount == kMaxTexcoordCount)
			{
				break;
			}
		}
	}

	*exportTexcoordCount = texcoordCount;

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

void OpenGexExport::CalculateMorphNormalArray(int vertexCount, int triangleCount, const int *indexTable, const ExportVertex *exportVertex, const Point3 *morphVertex, Point3 *morphNormal)
{
	for (int i = 0; i < vertexCount; i++)
	{
		morphNormal[i].Set(0.0F, 0.0F, 0.0F);
	}

	for (int i = 0; i < triangleCount; i++)
	{
		unsigned int k1 = indexTable[0];
		unsigned int k2 = indexTable[1];
		unsigned int k3 = indexTable[2];

		const Point3& v1 = morphVertex[exportVertex[k1].index];
		const Point3& v2 = morphVertex[exportVertex[k2].index];
		const Point3& v3 = morphVertex[exportVertex[k3].index];

		Point3 n = (v2 - v1) ^ (v3 - v1);
		morphNormal[k1] += n;
		morphNormal[k2] += n;
		morphNormal[k3] += n;

		indexTable += 3;
	}

	for (int i = 0; i < vertexCount; i++)
	{
		morphNormal[i].Unify();
	}
}

void OpenGexExport::ProcessNode(INode *node, bool exportAllFlag)
{
	if ((exportAllFlag) || (node->Selected()))
	{
		int type = GetNodeType(node);

		int size = (int) nodeArray->size();
		nodeArray->push_back(NodeReference(node, type, (std::string("node") += std::to_string(size + 1)).c_str()));
	}

	int subnodeCount = node->NumberOfChildren();
	for (int i = 0; i < subnodeCount; i++)
	{
		ProcessNode(node->GetChildNode(i), exportAllFlag);
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
			Object *object = nodeRef->node->GetObjectRef();
			if (object)
			{
				ISkin *skin = GetSkinInterface(object);
				if (skin)
				{
					int boneCount = skin->GetNumBones();
					for (int k = 0; k < boneCount; k++)
					{
						INode *node = skin->GetBone(k);
						if (node)
						{
							// If a node is used as a bone, then we force its type to be a bone.

							NodeReference *boneRef = FindNode(node);
							if (boneRef)
							{
								boneRef->nodeType = kNodeTypeBone;
							}
						}
					}
				}
			}

			nodeRef++;
		}
	}
}

template <class keyType> bool OpenGexExport::AnimationKeysDifferent(IKeyControl *keyInterface)
{
	keyType		key1, key2;

	keyInterface->GetKey(0, &key1);

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 1; i < keyCount; i++)
	{
		keyInterface->GetKey(i, &key2);
		if (!KeysEqual(key1, key2))
		{
			return (true);
		}
	}

	return (false);
}

template <class keyType> bool OpenGexExport::AnimationTangentsNonzero(IKeyControl *keyInterface)
{
	keyType		key;

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0; i < keyCount; i++)
	{
		keyInterface->GetKey(i, &key);
		if (KeyTangentsNonzero(key))
		{
			return (true);
		}
	}

	return (false);
}

bool OpenGexExport::AnimationPresent(Control *control)
{
	// This function determines whether a controller actually contains animation
	// by looking at all the keys to see whether they ever have different values.

	if (control)
	{
		IKeyControl *keyInterface = GetKeyControlInterface(control);
		if ((keyInterface) && (keyInterface->GetNumKeys() > 1))
		{
			ULONG classID = control->ClassID().PartA();

			if (classID == LININTERP_FLOAT_CLASS_ID)
			{
				return (AnimationKeysDifferent<ILinFloatKey>(keyInterface));
			}
			else if (classID == HYBRIDINTERP_FLOAT_CLASS_ID)
			{
				return ((AnimationKeysDifferent<IBezFloatKey>(keyInterface)) || (AnimationTangentsNonzero<IBezFloatKey>(keyInterface)));
			}
			else if (classID == TCBINTERP_FLOAT_CLASS_ID)
			{
				return (AnimationKeysDifferent<ITCBFloatKey>(keyInterface));
			}
			else if (classID == LININTERP_POSITION_CLASS_ID)
			{
				return (AnimationKeysDifferent<ILinPoint3Key>(keyInterface));
			}
			else if ((classID == HYBRIDINTERP_POSITION_CLASS_ID) || (classID == HYBRIDINTERP_POINT3_CLASS_ID))
			{
				return ((AnimationKeysDifferent<IBezPoint3Key>(keyInterface)) || (AnimationTangentsNonzero<IBezPoint3Key>(keyInterface)));
			}
			else if ((classID == TCBINTERP_POSITION_CLASS_ID) || (classID == TCBINTERP_POINT3_CLASS_ID))
			{
				return (AnimationKeysDifferent<ITCBPoint3Key>(keyInterface));
			}
			else if (classID == LININTERP_ROTATION_CLASS_ID)
			{
				return (AnimationKeysDifferent<ILinRotKey>(keyInterface));
			}
			else if (classID == HYBRIDINTERP_ROTATION_CLASS_ID)
			{
				return (AnimationKeysDifferent<IBezQuatKey>(keyInterface));
			}
			else if (classID == TCBINTERP_ROTATION_CLASS_ID)
			{
				return (AnimationKeysDifferent<ITCBRotKey>(keyInterface));
			}
			else if (classID == LININTERP_SCALE_CLASS_ID)
			{
				return (AnimationKeysDifferent<ILinScaleKey>(keyInterface));
			}
			else if (classID == HYBRIDINTERP_SCALE_CLASS_ID)
			{
				return ((AnimationKeysDifferent<IBezScaleKey>(keyInterface)) || (AnimationTangentsNonzero<IBezScaleKey>(keyInterface)));
			}
			else if (classID == TCBINTERP_SCALE_CLASS_ID)
			{
				return (AnimationKeysDifferent<ITCBScaleKey>(keyInterface));
			}
		}
	}

	return (false);
}

template <class keyType> void OpenGexExport::ExportKeyTimes(IKeyControl *keyInterface)
{
	IndentWrite("Key {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		WriteFloat(TicksToSec(key.time));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportKeyTimeControlPoints(IKeyControl *keyInterface)
{
	keyType		key[2];

	IndentWrite("Key (kind = \"-control\") {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyInterface->GetKey((i > 0) ? i - 1 : 0, &key[0]);
		keyInterface->GetKey(i, &key[1]);

		float t1 = TicksToSec(key[0].time);
		float t2 = TicksToSec(key[1].time);
		WriteFloat(t2 - 0.333333F * (t2 - t1));

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
		keyInterface->GetKey(i, &key[0]);
		keyInterface->GetKey((i < keyCount - 1) ? i + 1 : keyCount - 1, &key[1]);

		float t1 = TicksToSec(key[0].time);
		float t2 = TicksToSec(key[1].time);
		WriteFloat(t1 + 0.333333F * (t2 - t1));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportFloatKeyTimeControlPoints(IKeyControl *keyInterface)
{
	IBezFloatKey	key[2];

	IndentWrite("Key (kind = \"-control\") {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyInterface->GetKey((i > 0) ? i - 1 : 0, &key[0]);
		keyInterface->GetKey(i, &key[1]);

		float t1 = TicksToSec(key[0].time);
		float t2 = TicksToSec(key[1].time);

		float len = (GetInTanType(key[1].flags) == BEZKEY_USER) ? key[1].inLength : 0.333333F;
		WriteFloat(t2 - len * (t2 - t1));

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
		keyInterface->GetKey(i, &key[0]);
		keyInterface->GetKey((i < keyCount - 1) ? i + 1 : keyCount - 1, &key[1]);

		float t1 = TicksToSec(key[0].time);
		float t2 = TicksToSec(key[1].time);

		float len = (GetOutTanType(key[0].flags) == BEZKEY_USER) ? key[0].outLength : 0.333333F;
		WriteFloat(t1 + len * (t2 - t1));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportFloatKeyValues(IKeyControl *keyInterface, float scale)
{
	IndentWrite("Key {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		WriteFloat(key.val * scale);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportFloatKeyValueControlPoints(IKeyControl *keyInterface, float scale)
{
	IBezFloatKey	key[2];

	IndentWrite("Key (kind = \"-control\") {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyInterface->GetKey((i > 0) ? i - 1 : 0, &key[0]);
		keyInterface->GetKey(i, &key[1]);

		TimeValue t1 = key[0].time;
		TimeValue t2 = key[1].time;

		if (GetInTanType(key[1].flags) == BEZKEY_USER)
		{
			float dt = key[1].inLength * float(t2 - t1);
			WriteFloat((key[1].val + key[1].intan * dt) * scale);
		}
		else
		{
			WriteFloat(key[1].val * scale);
		}

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
		keyInterface->GetKey(i, &key[0]);
		keyInterface->GetKey((i < keyCount - 1) ? i + 1 : keyCount - 1, &key[1]);

		TimeValue t1 = key[0].time;
		TimeValue t2 = key[1].time;

		if (GetOutTanType(key[0].flags) == BEZKEY_USER)
		{
			float dt = key[0].outLength * float(t2 - t1);
			WriteFloat((key[0].val + key[0].outtan * dt) * scale);
		}
		else
		{
			WriteFloat(key[0].val * scale);
		}

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportPoint3KeyValues(IKeyControl *keyInterface)
{
	IndentWrite("Key {float[3] {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		WritePoint3(GetKeyPoint3(key));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportPoint3KeyValueControlPoints(IKeyControl *keyInterface)
{
	keyType		key[2];

	IndentWrite("Key (kind = \"-control\") {float[3] {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyInterface->GetKey((i > 0) ? i - 1 : 0, &key[0]);
		keyInterface->GetKey(i, &key[1]);

		TimeValue t1 = key[0].time;
		TimeValue t2 = key[1].time;

		if (GetInTanType(key[1].flags) == BEZKEY_USER)
		{
			Point3 dt = key[1].inLength * float(t2 - t1);
			WritePoint3(GetKeyPoint3(key[1]) + key[1].intan * dt);
		}
		else
		{
			WritePoint3(GetKeyPoint3(key[1]));
		}

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
	IndentWrite("Key (kind = \"+control\") {float[3] {");

	for (int i = 0;;)
	{
		keyInterface->GetKey(i, &key[0]);
		keyInterface->GetKey((i < keyCount - 1) ? i + 1 : keyCount - 1, &key[1]);

		TimeValue t1 = key[0].time;
		TimeValue t2 = key[1].time;

		if (GetOutTanType(key[0].flags) == BEZKEY_USER)
		{
			Point3 dt = key[0].outLength * float(t2 - t1);
			WritePoint3(GetKeyPoint3(key[0]) + key[0].outtan * dt);
		}
		else
		{
			WritePoint3(GetKeyPoint3(key[0]));
		}

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportQuatKeyValues(IKeyControl *keyInterface, bool relative)
{
	IndentWrite("Key {float[4] {");

	Quat prev(0.0F, 0.0F, 0.0F, 1.0F);

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		Quat q = GetKeyQuat(key);

		if (relative)
		{
			q = prev * q;
			prev = q;
		}

		WriteQuat(q);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportInvQuatKeyValues(IKeyControl *keyInterface)
{
	IndentWrite("Key {float[4] {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		WriteQuat(Quat(-key.val.q.x, -key.val.q.y, -key.val.q.z, key.val.q.w));

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

template <class keyType> void OpenGexExport::ExportFloatKeyData(IKeyControl *keyInterface, const char *kind, const float keyType::*data, float scale)
{
	IndentWrite("Key (kind = \"");
	Write(kind);
	Write("\") {float {");

	int keyCount = keyInterface->GetNumKeys();
	for (int i = 0;;)
	{
		keyType		key;

		keyInterface->GetKey(i, &key);
		WriteFloat(key.*data * scale);

		if (++i >= keyCount)
		{
			break;
		}

		Write(", ");
	}

	Write("}}\n");
}

void OpenGexExport::ExportAnimationTrack(Control *control, const char *target, bool newline, float scale)
{
	// This function exports a single animation track. The curve types for the
	// Time and Value structures depend on the controller's class ID.

	ULONG classID = control->ClassID().PartA();
	IKeyControl *keyInterface = GetKeyControlInterface(control);

	bool scaleOriented = false;

	IndentWrite("Track (target = %", 0, newline);
	Write(target);
	Write(")\n");
	IndentWrite("{\n");
	indentLevel++;

	if (classID == LININTERP_FLOAT_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ILinFloatKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportFloatKeyValues<ILinFloatKey>(keyInterface, scale);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == HYBRIDINTERP_FLOAT_CLASS_ID)
	{
		IndentWrite("Time (curve = \"bezier\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<IBezFloatKey>(keyInterface);
		ExportFloatKeyTimeControlPoints(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"bezier\")\n", -1);
		IndentWrite("{\n", -1);

		ExportFloatKeyValues<IBezFloatKey>(keyInterface, scale);
		ExportFloatKeyValueControlPoints(keyInterface, scale);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == TCBINTERP_FLOAT_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ITCBFloatKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"tcb\")\n", -1);
		IndentWrite("{\n", -1);

		ExportFloatKeyValues<ITCBFloatKey>(keyInterface, scale);

		ExportFloatKeyData<ITCBFloatKey>(keyInterface, "tension", &ITCBFloatKey::tens, scale);
		ExportFloatKeyData<ITCBFloatKey>(keyInterface, "continuity", &ITCBFloatKey::cont, scale);
		ExportFloatKeyData<ITCBFloatKey>(keyInterface, "bias", &ITCBFloatKey::bias, scale);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == LININTERP_POSITION_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ILinPoint3Key>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<ILinPoint3Key>(keyInterface);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if ((classID == HYBRIDINTERP_POSITION_CLASS_ID) || (classID == HYBRIDINTERP_POINT3_CLASS_ID))
	{
		IndentWrite("Time (curve = \"bezier\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<IBezPoint3Key>(keyInterface);
		ExportKeyTimeControlPoints<IBezPoint3Key>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"bezier\")\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<IBezPoint3Key>(keyInterface);
		ExportPoint3KeyValueControlPoints<IBezPoint3Key>(keyInterface);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if ((classID == TCBINTERP_POSITION_CLASS_ID) || (classID == TCBINTERP_POINT3_CLASS_ID))
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ITCBPoint3Key>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"tcb\")\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<ITCBPoint3Key>(keyInterface);

		ExportFloatKeyData<ITCBPoint3Key>(keyInterface, "tension", &ITCBPoint3Key::tens);
		ExportFloatKeyData<ITCBPoint3Key>(keyInterface, "continuity", &ITCBPoint3Key::cont);
		ExportFloatKeyData<ITCBPoint3Key>(keyInterface, "bias", &ITCBPoint3Key::bias);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == LININTERP_ROTATION_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ILinRotKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportQuatKeyValues<ILinRotKey>(keyInterface, true);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == HYBRIDINTERP_ROTATION_CLASS_ID)
	{
		IndentWrite("Time (curve = \"bezier\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<IBezQuatKey>(keyInterface);
		ExportKeyTimeControlPoints<IBezQuatKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportQuatKeyValues<IBezQuatKey>(keyInterface, true);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == TCBINTERP_ROTATION_CLASS_ID)
	{
		IndentWrite("Time (curve = \"tcb\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ITCBRotKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportQuatKeyValues<ITCBRotKey>(keyInterface, true);

		ExportFloatKeyData<ITCBRotKey>(keyInterface, "tension", &ITCBRotKey::tens);
		ExportFloatKeyData<ITCBRotKey>(keyInterface, "continuity", &ITCBRotKey::cont);
		ExportFloatKeyData<ITCBRotKey>(keyInterface, "bias", &ITCBRotKey::bias);

		indentLevel--;
		IndentWrite("}\n");
	}
	else if (classID == LININTERP_SCALE_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ILinScaleKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<ILinScaleKey>(keyInterface);

		indentLevel--;
		IndentWrite("}\n");

		scaleOriented = true;
	}
	else if (classID == HYBRIDINTERP_SCALE_CLASS_ID)
	{
		IndentWrite("Time (curve = \"bezier\")\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<IBezScaleKey>(keyInterface);
		ExportKeyTimeControlPoints<IBezScaleKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"bezier\")\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<IBezScaleKey>(keyInterface);
		ExportPoint3KeyValueControlPoints<IBezScaleKey>(keyInterface);

		indentLevel--;
		IndentWrite("}\n");

		scaleOriented = true;
	}
	else if (classID == TCBINTERP_SCALE_CLASS_ID)
	{
		IndentWrite("Time\n");
		IndentWrite("{\n");
		indentLevel++;

		ExportKeyTimes<ITCBScaleKey>(keyInterface);

		IndentWrite("}\n\n", -1);
		IndentWrite("Value (curve = \"tcb\")\n", -1);
		IndentWrite("{\n", -1);

		ExportPoint3KeyValues<ITCBScaleKey>(keyInterface);

		ExportFloatKeyData<ITCBScaleKey>(keyInterface, "tension", &ITCBScaleKey::tens);
		ExportFloatKeyData<ITCBScaleKey>(keyInterface, "continuity", &ITCBScaleKey::cont);
		ExportFloatKeyData<ITCBScaleKey>(keyInterface, "bias", &ITCBScaleKey::bias);

		indentLevel--;
		IndentWrite("}\n");

		scaleOriented = true;
	}

	indentLevel--;
	IndentWrite("}\n");

	// If scale keys were exported above, then we also need to export keys for
	// the quaternion orientation component.

	if (scaleOriented)
	{
		IndentWrite("Track (target = %orient)\n", 0, true);
		IndentWrite("{\n");
		indentLevel++;

		if (classID == LININTERP_SCALE_CLASS_ID)
		{
			IndentWrite("Time\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<ILinScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportQuatKeyValues<ILinScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}
		else if (classID == HYBRIDINTERP_SCALE_CLASS_ID)
		{
			IndentWrite("Time (curve = \"bezier\")\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<IBezScaleKey>(keyInterface);
			ExportKeyTimeControlPoints<IBezScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportQuatKeyValues<IBezScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}
		else
		{
			IndentWrite("Time\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<ITCBScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportQuatKeyValues<ITCBScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}

		indentLevel--;
		IndentWrite("}\n\n");

		IndentWrite("Track (target = %inv_orient)\n");
		IndentWrite("{\n");
		indentLevel++;

		if (classID == LININTERP_SCALE_CLASS_ID)
		{
			IndentWrite("Time\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<ILinScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportInvQuatKeyValues<ILinScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}
		else if (classID == HYBRIDINTERP_SCALE_CLASS_ID)
		{
			IndentWrite("Time (curve = \"bezier\")\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<IBezScaleKey>(keyInterface);
			ExportKeyTimeControlPoints<IBezScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportInvQuatKeyValues<IBezScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}
		else
		{
			IndentWrite("Time\n");
			IndentWrite("{\n");
			indentLevel++;

			ExportKeyTimes<ITCBScaleKey>(keyInterface);

			IndentWrite("}\n\n", -1);
			IndentWrite("Value\n", -1);
			IndentWrite("{\n", -1);

			ExportInvQuatKeyValues<ITCBScaleKey>(keyInterface);

			indentLevel--;
			IndentWrite("}\n");
		}

		indentLevel--;
		IndentWrite("}\n");
	}
}

void OpenGexExport::ExportSampledAnimation(INode *node)
{
	// This function exports animation as full 4x4 matrices sampled at the current frame rate.

	int frameTime = GetTicksPerFrame();

	IndentWrite("Animation\n", 0, true);
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("Track (target = %transform)\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("Time\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("Key {float {");

	int keyCount = (endTime - startTime) / frameTime;
	for (int i = 0; i < keyCount; i++)
	{
		WriteFloat(TicksToSec(i * frameTime + startTime));
		Write(", ");
	}

	WriteFloat(TicksToSec(endTime));
	Write("}}\n");

	IndentWrite("}\n\n", -1);
	IndentWrite("Value\n", -1);
	IndentWrite("{\n", -1);

	IndentWrite("Key\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[16]\n");
	IndentWrite("{\n");

	INode *parent = node->GetParentNode();

	for (int i = 0; i < keyCount; i++)
	{
		TimeValue time = i * frameTime + startTime;

		Matrix3 matrix = node->GetNodeTM(time);
		if (parent)
		{
			matrix *= Inverse(parent->GetNodeTM(time));
		}

		WriteMatrixFlat(matrix);
		Write(",\n");
	}

	Matrix3 matrix = node->GetNodeTM(endTime);
	if (parent)
	{
		matrix *= Inverse(parent->GetNodeTM(endTime));
	}

	WriteMatrixFlat(matrix);
	IndentWrite("}\n", 0, true);

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	IndentWrite("}\n");
}

void OpenGexExport::ExportObjectTransform(INode *node)
{
	Matrix3 matrix(true);
	matrix.SetRow(3, node->GetObjOffsetPos());
	PreRotateMatrix(matrix, node->GetObjOffsetRot());
	ApplyScaling(matrix, node->GetObjOffsetScale());

	matrix.ValidateFlags();
	if (!matrix.IsIdentity())
	{
		IndentWrite("Transform (object = true)\n", 0, true);
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

void OpenGexExport::ExportTransform(INode *node)
{
	// This function determines whether any animation needs to be exported
	// and writes the node transform in the appropriate form. This is followed
	// by the object transform and the animation tracks.

	Control *positionControl = nullptr;
	Control *rotationControl = nullptr;
	Control *scaleControl = nullptr;
	Control *posControl[3] = {nullptr, nullptr, nullptr};
	Control *rotControl[3] = {nullptr, nullptr, nullptr};

	bool positionAnimated = false;
	bool rotationAnimated = false;
	bool scaleAnimated = false;
	bool positionSubanimated = false;
	bool rotationSubanimated = false;
	bool posAnimated[3] = {false, false, false};
	bool rotAnimated[3] = {false, false, false};

	bool sampledAnimation = false;
	int eulerOrder = EULERTYPE_XYZ;

	Control *control = node->GetTMController();
	if (control)
	{
		positionControl = control->GetPositionController();
		if (positionControl)
		{
			if (positionControl->SuperClassID() == CTRL_POSITION_CLASS_ID)
			{
				posControl[0] = positionControl->GetXController();
				posControl[1] = positionControl->GetYController();
				posControl[2] = positionControl->GetZController();

				if ((posControl[0]) && (posControl[1]) && (posControl[2]) && (posControl[0]->SuperClassID() == CTRL_FLOAT_CLASS_ID) && (posControl[1]->SuperClassID() == CTRL_FLOAT_CLASS_ID) && (posControl[2]->SuperClassID() == CTRL_FLOAT_CLASS_ID))
				{
					positionAnimated = AnimationPresent(positionControl);
					posAnimated[0] = AnimationPresent(posControl[0]);
					posAnimated[1] = AnimationPresent(posControl[1]);
					posAnimated[2] = AnimationPresent(posControl[2]);

					positionSubanimated = posAnimated[0] | posAnimated[1] | posAnimated[2];
					positionAnimated |= positionSubanimated;
				}
				else
				{
					sampledAnimation = true;
				}
			}
			else
			{
				sampledAnimation = true;
			}
		}

		rotationControl = control->GetRotationController();
		if (rotationControl)
		{
			if (rotationControl->SuperClassID() == CTRL_ROTATION_CLASS_ID)
			{
				IEulerControl *eulerInterface = static_cast<IEulerControl *>(rotationControl->GetInterface(I_EULERCTRL));
				if (eulerInterface)
				{
					eulerOrder = eulerInterface->GetOrder();
					if (eulerOrder >= EULERTYPE_XYX)
					{
						eulerOrder = EULERTYPE_XYZ;
					}
				}

				rotControl[0] = rotationControl->GetXController();
				rotControl[1] = rotationControl->GetYController();
				rotControl[2] = rotationControl->GetZController();

				if ((rotControl[0]) && (rotControl[1]) && (rotControl[2]) && (rotControl[0]->SuperClassID() == CTRL_FLOAT_CLASS_ID) && (rotControl[1]->SuperClassID() == CTRL_FLOAT_CLASS_ID) && (rotControl[2]->SuperClassID() == CTRL_FLOAT_CLASS_ID))
				{
					rotationAnimated = AnimationPresent(rotationControl);
					rotAnimated[0] = AnimationPresent(rotControl[0]);
					rotAnimated[1] = AnimationPresent(rotControl[1]);
					rotAnimated[2] = AnimationPresent(rotControl[2]);

					rotationSubanimated = rotAnimated[0] | rotAnimated[1] | rotAnimated[2];
					rotationAnimated |= rotationSubanimated;
				}
				else
				{
					sampledAnimation = true;
				}
			}
			else
			{
				sampledAnimation = true;
			}
		}

		scaleControl = control->GetScaleController();
		if (scaleControl)
		{
			if (scaleControl->SuperClassID() == CTRL_SCALE_CLASS_ID)
			{
				scaleAnimated = AnimationPresent(scaleControl);
			}
			else
			{
				sampledAnimation = true;
			}
		}

		if (control->ClassID() == IKCONTROL_CLASS_ID)
		{
			sampledAnimation = true;
		}
	}

	Matrix3 matrix = node->GetNodeTM(startTime);
	Matrix3 parentMatrix(true);

	INode *parent = node->GetParentNode();
	if (parent)
	{
		parentMatrix = parent->GetNodeTM(startTime);
		matrix *= Inverse(parentMatrix);
	}

	if ((sampledAnimation) || ((!positionAnimated) && (!rotationAnimated) && (!scaleAnimated)))
	{
		// If there's no keyframe animation at all, then write the node transform as a single 4x4 matrix.
		// We might still be exporting sampled animation below.

		IndentWrite("Transform");

		if (sampledAnimation)
		{
			Write(" %transform");
		}

		IndentWrite("{\n", 0, true);
		indentLevel++;

		IndentWrite("float[16]\n");
		IndentWrite("{\n");
		WriteMatrix(matrix);
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");

		// The object-offset transform is always written separately because it is not inherited by subnodes.

		ExportObjectTransform(node);

		// Export a sampled animation if necessary.

		if ((sampledAnimation) && (control->SuperClassID() == CTRL_MATRIX3_CLASS_ID))
		{
			ExportSampledAnimation(node);
		}
	}
	else
	{
		// If there is some keyframe animation, then write the transform as factored position,
		// rotation, and scale followed by the non-animated object-offset transformation.

		static const char *const subtranslationName[3] =
		{
			"xpos", "ypos", "zpos"
		};

		static const char *const subrotationName[3] =
		{
			"xrot", "yrot", "zrot"
		};

		static const char *const axisName[3] =
		{
			"x", "y", "z"
		};

		Interval		interval;
		Point3			position;
		Quat			rotation;
		ScaleValue		scale;
		float			rot[4];

		// Grab a default position, rotation, and scale in case there are any missing subcontrollers.

		TMComponentsArg components(&position, &interval, rot, &interval, &scale, &interval);
		control->GetLocalTMComponents(startTime, components, Matrix3Indirect(parentMatrix));

		if (components.rotRep == TMComponentsArg::kQuat)
		{
			rotation.Set(rot[0], rot[1], rot[2], rot[3]);
		}
		else
		{
			EulerToQuat(rot, rotation, components.rotRep);
		}

		bool structFlag = false;

		// Export the position as either one Translation structure of kind "xyz" or three
		// Translation structures of kinds "x", "y", and "z".

		if (positionControl)
		{
			interval.SetInfinite();
			positionControl->GetValue(startTime, &position, interval);
		}

		if (positionSubanimated)
		{
			// When the position has subcontrollers, write the x, y, and z components separately
			// so they can be targeted by different tracks having different sets of keys.

			for (int i = 0; i < 3; i++)
			{
				float pos = position[i];

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
		else if ((positionAnimated) || (fabs(position.x) > kExportEpsilon) || (fabs(position.y) > kExportEpsilon) || (fabs(position.z) > kExportEpsilon))
		{
			// When the position does not have subcontrollers, write it as a single 3D point.

			IndentWrite("Translation");
			if (positionAnimated)
			{
				Write(" %position");
			}

			IndentWrite("{\n", 0, true);
			IndentWrite("float[3] {", 1);
			WriteHexPoint3(position);
			Write("}\t\t// ");
			WritePoint3(position);
			IndentWrite("}\n", 0, true);

			structFlag = true;
		}

		// Export the rotation as either one Rotation structure of kind "quaternion" or three
		// Rotation structures of kinds "x", "y", and "z" in the proper order.

		if (rotationControl)
		{
			interval.SetInfinite();
			rotationControl->GetValue(startTime, &rotation, interval);
		}

		if (rotationSubanimated)
		{
			// When the rotation has subcontrollers, write three separate Euler angle rotations
			// so they can be targeted by different tracks having different sets of keys.

			static const char eulerAxis[EULERTYPE_XYX][3] =
			{
				{0, 1, 2}, {0, 2, 1}, {1, 2, 0}, {1, 0, 2}, {2, 0, 1}, {2, 1, 0}
			};

			for (int i = 2; i >= 0; i--)
			{
				int axis = eulerAxis[eulerOrder][i];
				if (rotControl[axis])
				{
					float	angle;

					interval.SetInfinite();
					rotControl[axis]->GetValue(startTime, &angle, interval);

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
		}
		else if ((rotationAnimated) || (rotation.IsIdentity() == 0))
		{
			// When the rotation does not have subcontrollers, write it as a single quaternion.

			IndentWrite("Rotation", 0, structFlag);
			if (rotationAnimated)
			{
				Write(" %rotation");
			}

			Write(" (kind = \"quaternion\")\n");
			IndentWrite("{\n");
			IndentWrite("float[4] {", 1);
			WriteHexQuat(rotation);
			Write("}\t\t// ");
			WriteQuat(rotation);
			IndentWrite("}\n", 0, true);

			structFlag = true;
		}

		// Export the scale as a Scale structure of kind "xyz". If the scale is oriented by a
		// non-identity quaternion, then the Scale structure is surrounded by two Rotation
		// structures that cause the scale to be applied in the right directions.

		if (scaleControl)
		{
			interval.SetInfinite();
			scaleControl->GetValue(startTime, &scale, interval);
		}

		if ((scaleAnimated) || (fabs(scale.s.x - 1.0F) > kExportEpsilon) || (fabs(scale.s.y - 1.0F) > kExportEpsilon) || (fabs(scale.s.z - 1.0F) > kExportEpsilon))
		{
			// The scale is always written as an (x,y,z) scale and quaternion orientation.

			bool scaleOriented = ((scaleAnimated) || (1.0F - scale.q.w > kExportEpsilon));

			if (scaleOriented)
			{
				Quat q(-scale.q.x, -scale.q.y, -scale.q.z, scale.q.w);

				IndentWrite("Rotation", 0, structFlag);
				if (scaleAnimated)
				{
					Write(" %inv_orient");
				}

				Write(" (kind = \"quaternion\")\n");
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuat(q);
				Write("}\t\t// ");
				WriteQuat(q);
				IndentWrite("}\n", 0, true);

				structFlag = true;
			}

			IndentWrite("Scale", 0, structFlag);
			if (scaleAnimated)
			{
				Write(" %scale");
			}

			IndentWrite("{\n", 0, true);
			IndentWrite("float[3] {", 1);
			WriteHexPoint3(scale.s);
			Write("}\t\t// ");
			WritePoint3(scale.s);
			IndentWrite("}\n", 0, true);

			structFlag = true;

			if (scaleOriented)
			{
				IndentWrite("Rotation", 0, structFlag);
				if (scaleAnimated)
				{
					Write(" %orient");
				}

				Write(" (kind = \"quaternion\")\n");
				IndentWrite("{\n");
				IndentWrite("float[4] {", 1);
				WriteHexQuat(scale.q);
				Write("}\t\t// ");
				WriteQuat(scale.q);
				IndentWrite("}\n", 0, true);
			}
		}

		// Export the object-offset transformation.

		ExportObjectTransform(node);

		// Export the animation tracks.

		IndentWrite("Animation (begin = ", 0, true);
		WriteFloat(TicksToSec(startTime));
		Write(", end = ");
		WriteFloat(TicksToSec(endTime));
		Write(")\n");
		IndentWrite("{\n");
		indentLevel++;

		structFlag = false;

		if (positionSubanimated)
		{
			for (int i = 0; i < 3; i++)
			{
				if (posAnimated[i])
				{
					ExportAnimationTrack(posControl[i], subtranslationName[i], structFlag);
					structFlag = true;
				}
			}
		}
		else if (positionAnimated)
		{
			ExportAnimationTrack(positionControl, "position", structFlag);
			structFlag = true;
		}

		if (rotationSubanimated)
		{
			for (int i = 0; i < 3; i++)
			{
				if (rotAnimated[i])
				{
					ExportAnimationTrack(rotControl[i], subrotationName[i], structFlag);
					structFlag = true;
				}
			}
		}
		else if (rotationAnimated)
		{
			ExportAnimationTrack(rotationControl, "rotation", structFlag);
			structFlag = true;
		}

		if (scaleAnimated)
		{
			ExportAnimationTrack(scaleControl, "scale", structFlag);
		}

		indentLevel--;
		IndentWrite("}\n");
	}
}

void OpenGexExport::ExportMaterialRef(Mtl *material, int index)
{
	if (material->ClassID().PartA() == DMTL_CLASS_ID)
	{
		StdMat *stdmat = static_cast<StdMat *>(material);
		MaterialReference *materialRef = FindMaterial(stdmat);
		if (!materialRef)
		{
			int size = (int) materialArray->size();
			materialArray->push_back(MaterialReference(stdmat, (std::string("material") += std::to_string(size + 1)).c_str()));
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
}

void OpenGexExport::ExportMorphWeights(MorphR3 *morpher)
{
	int channelCount = (int) morpher->chanBank.size();
	Control **channelControl = new Control *[channelCount];
	bool animatedFlag = false;

	morphChannel *channel = &morpher->chanBank.front();
	for (int k = 0; k < channelCount; k++)
	{
		channelControl[k] = nullptr;

		if (ActiveMorphChannel(channel))
		{
			Control *control = channel->cblock->GetController(0);
			if (AnimationPresent(control))
			{
				channelControl[k] = control;
				animatedFlag = true;
			}
		}

		channel++;
	}

	IndentWrite("MorphWeight (index = 0) {float {1}}\n", 0, true);

	int morphIndex = 1;
	channel = &morpher->chanBank.front();
	for (int k = 0; k < channelCount; k++)
	{
		if (ActiveMorphChannel(channel))
		{
			float		weight;
			Interval	interval;

			IndentWrite("MorphWeight");

			if (animatedFlag)
			{
				Write(" %mw");
				WriteInt(morphIndex);
			}

			Write(" (index = ");
			WriteInt(morphIndex);
			Write(") {float {");

			interval.SetInfinite();
			channel->cblock->GetValue(0, startTime, weight, interval);
			WriteFloat(weight * 0.01F);

			Write("}}\n");

			morphIndex++;
		}

		channel++;
	}

	if (animatedFlag)
	{
		IndentWrite("Animation (begin = ", 0, true);
		WriteFloat(TicksToSec(startTime));
		Write(", end = ");
		WriteFloat(TicksToSec(endTime));
		Write(")\n");
		IndentWrite("{\n");
		indentLevel++;

		morphIndex = 1;
		bool structFlag = false;

		channel = &morpher->chanBank.front();
		for (int k = 0; k < channelCount; k++)
		{
			if (ActiveMorphChannel(channel))
			{
				Control *control = channelControl[k];
				if (control)
				{
					ExportAnimationTrack(control, (std::string("mw") += std::to_string(morphIndex)).c_str(), structFlag, 0.01F);
					structFlag = true;
				}

				morphIndex++;
			}

			channel++;
		}

		indentLevel--;
		IndentWrite("}\n");
	}

	delete[] channelControl;
}

void OpenGexExport::ExportNode(INode *node)
{
	// This function exports a single node in the scene and includes its name,
	// object reference, material references (for geometries), and transform.
	// Subnodes are then exported recursively.

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

		if (type == kNodeTypeGeometry)
		{
			bool visibleFlag = (node->GetVisibility(startTime) > 0.0F);
			bool shadowFlag = (node->CastShadows() != 0);
			bool motionBlurFlag = (node->GetMotBlurOnOff(startTime) != 0);

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
		}

		IndentWrite("{\n", 0, true);
		indentLevel++;

		INode *node = nodeRef->node;
		bool structFlag = false;

		// Export the node's name if it has one.

		const MCHAR *name = node->GetName();
		if ((name) && (name[0] != 0))
		{
			IndentWrite("Name {string {\"");
			Write(name);
			Write("\"}}\n");

			structFlag = true;
		}

		// Export the object reference and material references.

		if (type == kNodeTypeGeometry)
		{
			Object *object = node->GetObjectRef();
			ObjectReference *objectRef = FindObject(geometryArray, object);
			if (!objectRef)
			{
				int size = (int) geometryArray->size();
				geometryArray->push_back(ObjectReference(object, (std::string("geometry") += std::to_string(size + 1)).c_str(), node));
				objectRef = &geometryArray->at(size);
			}
			else
			{
				objectRef->nodeTable.push_back(node);
			}

			IndentWrite("ObjectRef {ref {$");
			Write(objectRef->structName.c_str());
			Write("}}\n");

			Mtl *material = node->GetMtl();
			if (material)
			{
				if (!material->IsMultiMtl())
				{
					ExportMaterialRef(material);
				}
				else
				{
					int materialCount = material->NumSubMtls();
					for (int i = 0; i < materialCount; i++)
					{
						ExportMaterialRef(material->GetSubMtl(i), i);
					}
				}
			}

			MorphR3 *morpher = GetMorphModifier(object);
			if (morpher)
			{
				ExportMorphWeights(morpher);
			}

			structFlag = true;
		}
		else if (type == kNodeTypeLight)
		{
			Object *object = node->GetObjectRef();
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
			Object *object = node->GetObjectRef();
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

		ExportTransform(node);
	}

	// Recursively export the subnodes.

	int subnodeCount = node->NumberOfChildren();
	for (int i = 0; i < subnodeCount; i++)
	{
		ExportNode(node->GetChildNode(i));
	}

	if (nodeRef)
	{
		indentLevel--;
		IndentWrite("}\n");
	}
}

void OpenGexExport::ExportSkin(ISkin *skin, INode *node, int vertexCount, const ExportVertex *exportVertex)
{
	// This function exports all skinning data, which includes the skeleton
	// and per-vertex bone influence data.

	IndentWrite("Skin\n", 0, true);
	IndentWrite("{\n");
	indentLevel++;

	// Write the skin bind pose transform.

	IndentWrite("Transform\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[16]\n");
	IndentWrite("{\n");

	Matrix3 matrix(true);
	skin->GetSkinInitTM(node, matrix, true);
	WriteMatrix(matrix);
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

	int boneCount = skin->GetNumBones();

	IndentWrite("ref\t\t\t// ");
	WriteInt(boneCount);
	IndentWrite("{\n", 0, true);
	IndentWrite("", 1);

	for (int i = 0; i < boneCount; i++)
	{
		const NodeReference *boneRef = nullptr;

		INode *bone = skin->GetBone(i);
		if (bone)
		{
			boneRef = FindNode(bone);
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

	IndentWrite("Transform\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("float[16]\t// ");
	WriteInt(boneCount);
	IndentWrite("{\n", 0, true);

	for (int i = 0; i < boneCount; i++)
	{
		Matrix3 matrix(true);

		INode *bone = skin->GetBone(i);
		if (bone)
		{
			skin->GetBoneInitTM(bone, matrix);
		}

		WriteHexMatrixFlat(matrix);

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

	ISkinContextData *skinContext = skin->GetContextInterface(node);

	int weightCount = 0;
	int *countArray = new int[vertexCount];

	for (int i = 0; i < vertexCount; i++)
	{
		int count = skinContext->GetNumAssignedBones(exportVertex[i].index);
		countArray[i] = count;
		weightCount += count;
	}

	// Write the bone count array. There is one entry per vertex.

	IndentWrite("BoneCountArray\n");
	IndentWrite("{\n");
	indentLevel++;

	IndentWrite("u16\t\t// ");
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
		int count = countArray[i];
		for (int j = 0; j < count; j++)
		{
			index[j] = skinContext->GetAssignedBone(exportVertex[i].index, j);
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
		int count = countArray[i];
		for (int j = 0; j < count; j++)
		{
			weight[j] = skinContext->GetBoneWeight(exportVertex[i].index, j);
		}

		weight += count;
	}

	IndentWrite("float\t\t// ");
	WriteInt(weightCount);
	IndentWrite("{\n", 0, true);
	WriteFloatArray(weightCount, weightArray);
	IndentWrite("}\n");

	delete[] weightArray;

	indentLevel--;
	IndentWrite("}\n");

	delete[] countArray;

	indentLevel--;
	IndentWrite("}\n");
}

void OpenGexExport::ExportGeometry(const ObjectReference *objectRef)
{
	// This function exports a single geometry object.

	int		triangleCount, colorCount, texcoordCount;

	Write("\nGeometryObject $");
	Write(objectRef->structName.c_str());
	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	Object *directObject = objectRef->object;
	Object *object = directObject->Eval(startTime).obj;
	Object *baseObject = nullptr;

	TriObject *triObject = static_cast<TriObject *>(object->ConvertToType(startTime, Class_ID(TRIOBJ_CLASS_ID, 0)));
	TriObject *baseTriObject = nullptr;

	Mesh *mesh = &triObject->GetMesh();
	Mesh *baseMesh = mesh;

	ISkin *skin = GetSkinInterface(directObject);
	if (skin)
	{
		// Get the object containing the vertex positions before they are deformed
		// by the skin modifier. We need this in order to export the proper bind pose.

		baseObject = directObject->FindBaseObject();
		baseTriObject = static_cast<TriObject *>(baseObject->ConvertToType(startTime, Class_ID(TRIOBJ_CLASS_ID, 0)));
		baseMesh = &baseTriObject->GetMesh();

		if (baseMesh->getNumVerts() != mesh->getNumVerts())
		{
			baseMesh = mesh;
		}
	}

	bool structFlag = false;

	MorphR3 *morpher = GetMorphModifier(directObject);
	if (morpher)
	{
		int morphIndex = 1;
		int channelCount = (int) morpher->chanBank.size();
		morphChannel *channel = &morpher->chanBank.front();
		for (int k = 0; k < channelCount; k++)
		{
			if (ActiveMorphChannel(channel))
			{
				IndentWrite("Morph (index = ", 0, structFlag);
				WriteInt(morphIndex);
				Write(", base = 0)\n");
				IndentWrite("{\n");
				IndentWrite("Name {string {\"", 1);
				Write(channel->mName);
				Write("\"}}\n");
				IndentWrite("}\n");

				structFlag = true;
				morphIndex++;
			}

			channel++;
		}
	}

	IndentWrite("Mesh (primitive = \"triangles\")\n", 0, structFlag);
	IndentWrite("{\n");
	indentLevel++;

	ExportVertex *exportVertex = DeindexMesh(mesh, baseMesh, &triangleCount, &colorCount, &texcoordCount);
	ExportVertex *unifiedVertex = new ExportVertex[triangleCount * 3];
	int *indexTable = new int[triangleCount * 3];
	int unifiedCount = UnifyVertices(triangleCount * 3, exportVertex, unifiedVertex, indexTable);

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

	// Write the color array if it exists.

	if (colorCount == 1)
	{
		IndentWrite("VertexArray (attrib = \"color\")\n", 0, true);
		IndentWrite("{\n");
		indentLevel++;

		IndentWrite("float[3]\t\t// ");
		WriteInt(unifiedCount);
		IndentWrite("{\n", 0, true);
		WriteVertexArray(unifiedCount, &unifiedVertex->color, sizeof(ExportVertex));
		IndentWrite("}\n");

		indentLevel--;
		IndentWrite("}\n");
	}

	// Write the texcoord arrays.

	for (int k = 0; k < texcoordCount; k++)
	{
		IndentWrite("VertexArray (attrib = \"texcoord", 0, true);

		if (k != 0)
		{
			Write("[");
			WriteInt(k);
			Write("]");
		}

		Write("\")\n");

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

	if (morpher)
	{
		Point3 *morphNormal = new Point3[unifiedCount];

		int morphIndex = 1;
		int channelCount = (int) morpher->chanBank.size();
		morphChannel *channel = &morpher->chanBank.front();
		for (int k = 0; k < channelCount; k++)
		{
			if (ActiveMorphChannel(channel))
			{
				if (channel->mPoints.size() == baseMesh->getNumVerts())
				{
					const Point3 *morphVertex = &channel->mPoints.front();
					CalculateMorphNormalArray(unifiedCount, triangleCount, indexTable, unifiedVertex, morphVertex, morphNormal);

					// Write the morph target position array.

					IndentWrite("VertexArray (attrib = \"position\", morph = ", 0, true);
					WriteInt(morphIndex);
					Write(")\n");
					IndentWrite("{\n");
					indentLevel++;

					IndentWrite("float[3]\t\t// ");
					WriteInt(unifiedCount);
					IndentWrite("{\n", 0, true);
					WriteMorphVertexArray(unifiedCount, unifiedVertex, morphVertex);
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
					WriteMorphNormalArray(unifiedCount, morphNormal);
					IndentWrite("}\n");

					indentLevel--;
					IndentWrite("}\n");
				}

				morphIndex++;
			}

			channel++;
		}

		delete[] morphNormal;
	}

	// Write the index arrays.

	unsigned int maxMatID = 0;
	Face *triangle = mesh->faces;
	for (int i = 0; i < triangleCount; i++)
	{
		MtlID id = triangle[i].getMatID();
		if (id > maxMatID)
		{
			maxMatID = id;
		}
	}

	if (maxMatID == 0)
	{
		// There is only one material, so write a single index array.

		IndentWrite("IndexArray\n", 0, true);
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
		// If there are multiple material IDs, then write a separate
		// index array for each one.

		int *materialTriangleCount = new int[maxMatID + 1];
		memset(materialTriangleCount, 0, (maxMatID + 1) * sizeof(int));

		for (int i = 0; i < triangleCount; i++)
		{
			materialTriangleCount[triangle[i].getMatID()]++;
		}

		int *materialIndexTable = new int[triangleCount * 3];

		for (unsigned int m = 0; m <= maxMatID; m++)
		{
			if (materialTriangleCount[m] != 0)
			{
				int materialIndexCount = 0;
				for (int i = 0; i < triangleCount; i++)
				{
					if (triangle[i].getMatID() == m)
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
		ExportSkin(skin, objectRef->nodeTable.front(), unifiedCount, unifiedVertex);
	}

	// Clean up.

	delete[] indexTable;
	delete[] unifiedVertex;
	delete[] exportVertex;

	if (baseTriObject != baseObject)
	{
		baseTriObject->DeleteMe();
	}

	if (triObject != object)
	{
		triObject->DeleteMe();
	}

	indentLevel--;
	IndentWrite("}\n");

	indentLevel--;
	Write("}\n");
}

void OpenGexExport::ExportLight(const ObjectReference *objectRef)
{
	// This function exports a single light object.

	Write("\nLightObject $");
	Write(objectRef->structName.c_str());

	GenLight *object = static_cast<GenLight *>(objectRef->object);

	Write(" (type = ");
	bool pointFlag = false;
	bool spotFlag = false;

	if (object->IsSpot())
	{
		Write("\"spot\"");
		pointFlag = true;
		spotFlag = true;
	}
	else if (object->IsDir())
	{
		Write("\"infinite\"");
	}
	else
	{
		Write("\"point\"");
		pointFlag = true;
	}

	if (object->GetShadow() == 0)
	{
		Write(", shadow = false");
	}

	Write(")");
	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	// Export the light's color, and include a separate intensity if necessary.

	IndentWrite("Color (attrib = \"light\") {float[3] {");
	WriteColor(object->GetRGBColor(startTime));
	Write("}}\n");

	float intensity = object->GetIntensity(startTime);
	if (intensity != 1.0F)
	{
		IndentWrite("Param (attrib = \"intensity\") {float {");
		WriteFloat(intensity);
		Write("}}\n");
	}

	if ((spotFlag) && (object->GetProjector() != 0))
	{
		// If a spot light has a projector, then export a texture.

		Texmap *texmap = object->GetProjMap();
		if ((texmap) && (texmap->ClassID().PartA() == BMTEX_CLASS_ID))
		{
			BitmapTex *bitmap = static_cast<BitmapTex *>(texmap);
			const MCHAR *name = bitmap->GetMapName();
			if (name)
			{
				IndentWrite("Texture (attrib = \"projection\") {string {\"");
				WriteFileName(name);
				Write("\"}}\n");
			}
		}
	}

	if (pointFlag)
	{
		// Export a separate attenuation function for each type that's in use.

		int decay = object->GetDecayType();
		if (decay != DECAY_NONE)
		{
			IndentWrite("Atten (curve = \"", 0, true);
			Write((decay == DECAY_INV) ? "inverse\")\n" : "inverse_square\")\n");
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"scale\") {float {", 1);
			WriteFloat(object->GetDecayRadius(startTime));
			Write("}}\n");

			IndentWrite("}\n");
		}

		if (object->GetUseAtten())
		{
			IndentWrite("Atten (curve = \"smooth\")\n", 0, true);
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"begin\") {float {", 1);
			WriteFloat(object->GetAtten(startTime, ATTEN_START));
			Write("}}\n");

			IndentWrite("Param (attrib = \"end\") {float {", 1);
			WriteFloat(object->GetAtten(startTime, ATTEN_END));
			Write("}}\n");

			IndentWrite("}\n");
		}

		if (object->GetUseAttenNear())
		{
			IndentWrite("Atten (curve = \"smooth\")\n", 0, true);
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"begin\") {float {", 1);
			WriteFloat(object->GetAtten(startTime, ATTEN1_END));
			Write("}}\n");

			IndentWrite("Param (attrib = \"end\") {float {", 1);
			WriteFloat(object->GetAtten(startTime, ATTEN1_START));
			Write("}}\n");

			IndentWrite("}\n");
		}

		if (spotFlag)
		{
			// Export additional angular attenuation for spot lights.

			IndentWrite("Atten (kind = \"cos_angle\", curve = \"smooth\")\n", 0, true);
			IndentWrite("{\n");

			IndentWrite("Param (attrib = \"begin\") {float {", 1);
			WriteFloat(cos(object->GetHotspot(startTime) * (kDegToRad * 0.5F)));
			Write("}}\n");

			IndentWrite("Param (attrib = \"end\") {float {", 1);
			WriteFloat(cos(object->GetFallsize(startTime) * (kDegToRad * 0.5F)));
			Write("}}\n");

			IndentWrite("}\n");
		}
	}

	indentLevel--;
	Write("}\n");
}

void OpenGexExport::ExportCamera(const ObjectReference *objectRef)
{
	// This function exports a single camera object.

	Write("\nCameraObject $");
	Write(objectRef->structName.c_str());
	WriteNodeTable(objectRef);

	Write("\n{\n");
	indentLevel++;

	CameraObject *object = static_cast<CameraObject *>(objectRef->object);

	IndentWrite("Param (attrib = \"fov\") {float {");
	WriteFloat(object->GetFOV(startTime));
	Write("}}\n");

	IndentWrite("Param (attrib = \"near\") {float {");
	WriteFloat(object->GetClipDist(startTime, CAM_HITHER_CLIP));
	Write("}}\n");

	IndentWrite("Param (attrib = \"far\") {float {");
	WriteFloat(object->GetClipDist(startTime, CAM_YON_CLIP));
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

void OpenGexExport::ExportTexture(StdMat *material, int slot, const char *attrib)
{
	// This function exports a single texture from a material.

	Texmap *texmap = material->GetSubTexmap(slot);
	if ((texmap) && (texmap->ClassID().PartA() == BMTEX_CLASS_ID))
	{
		BitmapTex *bitmap = static_cast<BitmapTex *>(texmap);
		const MCHAR *name = bitmap->GetMapName();
		if (name)
		{
			IndentWrite("Texture (attrib = \"", 0, true);
			Write(attrib);
			Write("\"");

			if (bitmap->GetUVWSource() == UVWSRC_EXPLICIT)
			{
				int channel = bitmap->GetMapChannel();
				if (channel > 1)
				{
					Write(", texcoord = ");
					WriteInt(channel - 1);
				}
			}

			Write(")\n");
			IndentWrite("{\n");
			indentLevel++;

			IndentWrite("string {\"");
			WriteFileName(name);
			Write("\"}\n");

			// If the texture has a scale and/or offset, then export a coordinate transform.

			StdUVGen *gen = bitmap->GetUVGen();
			if (gen)
			{
				float uscale = gen->GetUScl(startTime);
				float vscale = gen->GetVScl(startTime);
				float uoffset = gen->GetUOffs(startTime);
				float voffset = gen->GetVOffs(startTime);

				if ((uscale != 1.0F) || (vscale != 1.0F) || (uoffset != 0.0F) || (voffset != 0.0F))
				{
					Matrix3 matrix(Point3(uscale, 0.0F, 0.0F), Point3(0.0F, vscale, 0.0F), Point3(0.0F, 0.0F, 1.0F), Point3(uoffset, voffset, 0.0F));

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

			indentLevel--;
			IndentWrite("}\n");
		}
	}
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
			Write("\nMaterial $");
			Write(materialRef->structName.c_str());

			StdMat *material = materialRef->material;
			if (material->GetTwoSided())
			{
				Write(" (two_sided = true)");
			}

			Write("\n{\n");
			indentLevel++;

			IndentWrite("Name {string {\"");
			Write(material->GetName());
			Write("\"}}\n\n");

			IndentWrite("Color (attrib = \"diffuse\") {float[3] {");
			WriteColor(material->GetDiffuse(startTime));
			Write("}}\n");

			Color specular = material->GetSpecular(startTime) * material->GetShinStr(startTime);
			if ((specular.r > 0.0F) || (specular.g > 0.0F) | (specular.b > 0.0F))
			{
				IndentWrite("Color (attrib = \"specular\") {float[3] {");
				WriteColor(specular);
				Write("}}\n");

				IndentWrite("Param (attrib = \"specular_power\") {float {");
				WriteFloat(material->GetShininess(startTime) * 100.0F);
				Write("}}\n");
			}

			if (material->GetSelfIllumColorOn())
			{
				IndentWrite("Color (attrib = \"emission\") {float[3] {");
				WriteColor(material->GetSelfIllumColor());
				Write("}}\n");
			}

			ExportTexture(material, ID_DI, "diffuse");
			ExportTexture(material, ID_SP, "specular");
			ExportTexture(material, ID_SI, "emission");
			ExportTexture(material, ID_OP, "opacity");
			ExportTexture(material, ID_BU, "normal");

			indentLevel--;
			Write("}\n");

			materialRef++;
		}
	}
}

void OpenGexExport::ExportMetrics(void)
{
	float scale = float(GetMasterScale(UNITS_METERS));

	Write("Metric (key = \"distance\") {float {");
	WriteFloat(scale);
	Write("}}\n");

	Write("Metric (key = \"angle\") {float {1}}\n");
	Write("Metric (key = \"time\") {float {1}}\n");
	Write("Metric (key = \"up\") {string {\"z\"}}\n");
}


BOOL WINAPI DllMain(HINSTANCE hinstDLL, ULONG fdwReason, LPVOID lpvReserved)
{
	if (fdwReason == DLL_PROCESS_ATTACH)
	{
		DisableThreadLibraryCalls(hinstDLL);
	}

	return (TRUE);
}

__declspec(dllexport) int LibNumberClasses(void)
{
	return (1);
}

__declspec(dllexport) ClassDesc *LibClassDesc(int i)
{
	if (i == 0)
	{
		return (&TheClassDesc);
	}

	return (nullptr);
}

__declspec(dllexport) const TCHAR *LibDescription(void)
{
	return (L"OpenGEX Exporter");
}

__declspec(dllexport) ULONG LibVersion(void)
{
	return (VERSION_3DSMAX);
}

__declspec(dllexport) int LibInitialize(void)
{
	return (TRUE);
}

__declspec(dllexport) int LibShutdown(void)
{
	return (0);
}
