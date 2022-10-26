//
// OpenGEX exporter for Maya
// Version 3.0
//
// This file is part of the Open Game Engine Exchange library, by Eric Lengyel.
// Copyright 2013-2022, Terathon Software LLC
//
// This software is distributed under the MIT License.
// Separate proprietary licenses are available from Terathon Software.
//


#ifndef OpenGex_Maya_h
#define OpenGex_Maya_h


#include <windows.h>
#include <vector>
#include <sstream>
#include "maya/MGlobal.h"
#include "maya/MIOStream.h"
#include "maya/MPxFileTranslator.h"
#include "maya/MAnimControl.h"
#include "maya/MSelectionList.h"
#include "maya/MMatrix.h"
#include "maya/MEulerRotation.h"
#include "maya/MQuaternion.h"
#include "maya/MFloatArray.h"
#include "maya/MFloatVectorArray.h"
#include "maya/MFloatPointArray.h"
#include "maya/MPlugArray.h"
#include "maya/MDagPathArray.h"
#include "maya/MDagPath.h"
#include "maya/MItDependencyGraph.h"
#include "maya/MItDag.h"
#include "maya/MFnSet.h"
#include "maya/MFnDagNode.h"
#include "maya/MFnTransform.h"
#include "maya/MFnIkJoint.h"
#include "maya/MFnMesh.h"
#include "maya/MFnSkinCluster.h"
#include "maya/MFnBlendShapeDeformer.h"
#include "maya/MFnSpotLight.h"
#include "maya/MFnCamera.h"
#include "maya/MFnAttribute.h"
#include "maya/MFnAnimCurve.h"
#include "maya/MFnMatrixData.h"
#include "maya/MFnPhongShader.h"
#include "maya/MFnPlugin.h"


namespace OpenGex
{
	enum
	{
		kMaxVertexColorCount	= 2,
		kMaxTexcoordCount		= 2
	};


	enum
	{
		kNodeTypeNone = -1,
		kNodeTypeNode,
		kNodeTypeBone,
		kNodeTypeGeometry,
		kNodeTypeLight,
		kNodeTypeCamera,
		kNodeTypeCount
	};


	struct NodeReference
	{
		MObject			node;
		int				nodeType;
		int				childIndex;
		std::string		structName;

		NodeReference(const MObject& n, int type, int index, const char *name) : node(n), nodeType(type), childIndex(index), structName(name) {}
		NodeReference(const NodeReference& nodeReference) : node(nodeReference.node), nodeType(nodeReference.nodeType), childIndex(nodeReference.childIndex), structName(nodeReference.structName) {}
	};


	struct ObjectReference
	{
		MObject					object;
		std::string				structName;
		std::vector<MObject>	nodeTable;

		ObjectReference(const MObject& obj, const char *name, const MObject& node) : object(obj), structName(name), nodeTable(1, node) {}
		ObjectReference(const ObjectReference& objectReference) : object(objectReference.object), structName(objectReference.structName), nodeTable(objectReference.nodeTable) {}
	};


	struct MaterialReference
	{
		MObject					material;
		std::string				structName;

		MaterialReference(const MObject& mat, const char *name) : material(mat), structName(name) {}
		MaterialReference(const MaterialReference& materialReference) : material(materialReference.material), structName(materialReference.structName) {}
	};


	struct TextureReference
	{
		MObject					texture;
		int						texcoord;

		TextureReference(const MObject& tex, int coord) : texture(tex), texcoord(coord) {}
		TextureReference(const TextureReference& textureReference) : texture(textureReference.texture), texcoord(textureReference.texcoord) {}
	};


	struct ExportVertex
	{
		unsigned int	hash;
		unsigned int	vertexIndex;
		unsigned int	normalIndex;

		MFloatVector	position;
		MFloatVector	normal;
		MColor			color[kMaxVertexColorCount];
		float			texcoord[kMaxTexcoordCount][2];

		ExportVertex();

		bool operator ==(const ExportVertex& v) const;

		void Hash(void);
	};
}


class OpenGexExport : public MPxFileTranslator
{
	private:

		HANDLE			exportFile;
		int				indentLevel;

		std::vector<OpenGex::NodeReference>			*nodeArray;
		std::vector<OpenGex::ObjectReference>		*geometryArray;
		std::vector<OpenGex::ObjectReference>		*lightArray;
		std::vector<OpenGex::ObjectReference>		*cameraArray;
		std::vector<OpenGex::MaterialReference>		*materialArray;
		std::vector<OpenGex::TextureReference>		*textureArray;

		void Write(const void *buffer, unsigned int size) const;
		void Write(const char *string) const;
		void Write(const wchar_t *string) const;
		void IndentWrite(const char *string, int extra = 0, bool newline = false) const;

		void WriteInt(int i) const;
		void WriteUnsignedInt(unsigned int i) const;
		void WriteFloat(float f) const;
		void WriteHexFloat(float f) const;
		void WriteMatrix(const MMatrix& matrix) const;
		void WriteMatrixFlat(const MMatrix& matrix) const;
		void WriteHexMatrixFlat(const MMatrix& matrix) const;
		void WriteVector(const MVector& point) const;
		void WriteHexVector(const MVector& point) const;
		void WriteQuaternion(const MQuaternion& quat) const;
		void WriteHexQuaternion(const MQuaternion& quat) const;
		void WriteColor(const MColor& color) const;
		void WriteFileName(const char *string) const;

		void WriteIntArray(int count, const int *value) const;
		void WriteFloatArray(int count, const float *value) const;

		void WriteVertex(const float (& vertex)[2]) const;
		void WriteVertex(const MFloatVector& vertex) const;
		void WriteVertex(const MColor& vertex) const;
		template <class type> void WriteVertexArray(int count, const type *vertex, int stride) const;
		void WriteMorphVertexArray(int count, const OpenGex::ExportVertex *exportVertex, const MFloatPointArray& morphVertexArray);
		void WriteMorphNormalArray(int count, const OpenGex::ExportVertex *exportVertex, const MFloatVectorArray& morphNormalArray);

		void WriteTriangle(int triangleIndex, const int *indexTable) const;
		void WriteTriangleArray(int count, const int *indexTable) const;

		void WriteNodeTable(const OpenGex::ObjectReference *objectRef) const;

		int GetNodeType(const MObject& node, int *childIndex) const;
		static MFnSkinCluster *GetSkinCluster(const MObject& node);
		static bool FindSkinClusterInputGeometry(const MFnSkinCluster *skin, MObject *object);
		static MFnBlendShapeDeformer *GetBlendShapeDeformer(const MObject& node, unsigned int *geometryIndex = nullptr);
		static bool FindBlendShapeDeformerInputGeometry(const MFnBlendShapeDeformer *deformer, unsigned int geometryIndex, MObject *object);

		OpenGex::NodeReference *FindNode(const MObject& node) const;
		static OpenGex::ObjectReference *FindObject(std::vector<OpenGex::ObjectReference> *array, const MObject& object);
		OpenGex::MaterialReference *FindMaterial(const MObject& material);
		OpenGex::TextureReference *FindTexture(const MObject& texture);

		static int GetLocalIndex(int index, const MIntArray& globalIndexArray);
		OpenGex::ExportVertex *DeindexMesh(MFnMesh *mesh, const MFnMesh *baseMesh, int *exportTriangleCount, int *exportColorCount, int *exportTexcoordCount, int **polygonIndexArray);
		static int FindExportVertex(const std::vector<int>& bucket, const OpenGex::ExportVertex *exportVertex, const OpenGex::ExportVertex& vertex);
		static int UnifyVertices(int vertexCount, const OpenGex::ExportVertex *exportVertex, OpenGex::ExportVertex *unifiedVertex, int *indexTable);

		void ProcessNode(const MDagPath& dagPath, const MSelectionList *exportList);
		void ProcessSkinnedMeshes(void);

		static bool AnimationPresent(const MFnAnimCurve& animCurve);

		void ExportKeyTimes(const MFnAnimCurve& animCurve);
		void ExportKeyTimeControlPoints(const MFnAnimCurve& animCurve);
		void ExportKeyValues(const MFnAnimCurve& animCurve, float scale = 1.0F);
		void ExportKeyValueControlPoints(const MFnAnimCurve& animCurve, float scale = 1.0F);
		void ExportAnimationTrack(const MFnAnimCurve& animCurve, const char *target, bool newline, float scale = 1.0F);

		void ExportTransform(const MObject& node, const MObject& parent);
		void ExportMaterialRef(const MObject& material, int index);
		void ExportMorphWeights(const MObject& node, const MFnBlendShapeDeformer *deformer);
		void ExportNode(const MDagPath& dagPath, const MObject& parent);

		void ExportSkin(const MFnSkinCluster& skin, const MObject& object, int vertexCount, const OpenGex::ExportVertex *exportVertex);
		void ExportGeometry(const OpenGex::ObjectReference *objectRef);
		void ExportLight(const OpenGex::ObjectReference *objectRef);
		void ExportCamera(const OpenGex::ObjectReference *objectRef);
		void ExportObjects(void);

		bool ExportTexture(const MFnDependencyNode& shader, const char *input, const char *attrib);
		void ExportMaterials(void);

		void ExportMetrics(void);

	public:

		OpenGexExport();
		~OpenGexExport();

		static void *New(void);

		MStatus writer(const MFileObject& file, const MString& optionsString, FileAccessMode mode) override;
		bool haveWriteMethod(void) const override;
		MString defaultExtension(void) const override;
		MFileKind identifyFile(const MFileObject& file, const char *buffer, short size) const override;
};


#endif
