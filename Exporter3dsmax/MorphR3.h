// The morpher modifier is not part of the base Max SDK, and the header wm3.h
// supplied in the maxsdk/samples/modifiers/morpher/ directory does not build,
// so we include our own minimal header for it that lets us access what we need.


#ifndef __MORPHR3__H
#define __MORPHR3__H


#include "max.h"


#define MR3_CLASS_ID Class_ID(0x17BB6854, 0xA5CBA2A3)
#define MorphExport __declspec(dllimport)


class morphChannel;
class MorphR3;
class M3Mat;


// The std::vector class used by Max has the following layout.
// We use this class as a stand-in to maintain binary compatibility.

template <typename type> class StdVector
{
	private:

		type		*first;
		type		*last;
		type		*end;
		void		*reserved;

	public:

		size_t size(void) const
		{
			return (last - first);
		}

		type& front(void) const
		{
			return (*first);
		}
};


class TargetCache
{
	public:

		long					mNumPoints;
		INode					*mTargetINode;
		StdVector<Point3>		mTargetPoints;
		float					mTargetPercent;
};


class morphChannel
{
	public:

		~morphChannel();
		morphChannel();
		morphChannel(const morphChannel& from);

		MorphR3						*mp;

		float						mCurvature;
		int							mNumPoints;

		int							iTargetListSelection;

		StdVector<Point3>			mPoints;
		StdVector<Point3>			mDeltas;
		StdVector<double>			mWeights;
	
		StdVector<TargetCache>		mTargetCache;

		BitArray					mSel;
		INode						*mConnection;
		TSTR						mName;
		int							mNumProgressiveTargs;
		float						mTargetPercent;

		BOOL						mActive;
		BOOL						mModded;
		BOOL						mUseLimit;
		BOOL						mUseSel;
		float						mSpinmin, mSpinmax;

		BOOL						mInvalid;
		BOOL						mActiveOverride;

		IParamBlock					*cblock;

		void InitTargetCache(const int& targnum, INode *nd);
	
		MorphExport void ResetMe();
		MorphExport void AllocBuffers(int sizeA, int sizeB);
		MorphExport float getMemSize();
		MorphExport void rebuildChannel();
		MorphExport void buildFromNode(INode *node, BOOL resetTime = TRUE, TimeValue t = 0, BOOL picked = FALSE);

		MorphExport void operator =(const morphChannel& from);
		void operator =(const TargetCache& tcache);

		MorphExport IOResult Save(ISave *isave);
		MorphExport IOResult Load(ILoad *iload);

		void SetUpNewController();
		int NumProgressiveTargets(void);
		void ResetRefs(MorphR3 *, const int&);
		float GetTargetPercent(const int& which);
		void ReNormalize();
		void CopyTargetPercents(const morphChannel& chan);
};


class morphCache
{
	public:

		BOOL		CacheValid;
		Point3		*oPoints;
		double		*oWeights;
		BitArray	sel;
		int			Count;
};


class MorphR3 : public Modifier, TimeChangeCallback
{
	public:

		float						mFileVersion;

		static IObjParam			*ip;
		
		StdVector<morphChannel>		chanBank;
		M3Mat						*morphmaterial;
		
		int							chanSel;
		int							chanNum;

		ISpinnerControl				*chanSpins[10];
		ISpinnerControl				*glSpinmin, *glSpinmax;
		ISpinnerControl				*cSpinmin, *cSpinmax, *cCurvature, *cTargetPercent;

		IParamBlock					*pblock;

		HWND						hwGlobalParams, hwChannelList,	hwChannelParams, hwAdvanced, hwLegend;
		static HWND					hMaxWnd;

		ICustEdit					*newname;

		morphCache					MC_Local;

		BOOL						tccI;
		TCHAR						trimD[50];

		BOOL						recordModifications;
		int							recordTarget;

		Tab<int>					markerIndex;
		NameTab						markerName;
		int							markerSel;

		int							cOp;
		int							srcIdx;

		bool						hackUI;

		MorphR3();
		~MorphR3();

		void TimeChanged(TimeValue t);

		void DeleteThis();
		void GetClassName(TSTR& s);
		virtual Class_ID ClassID();	
		RefTargetHandle Clone(RemapDir& remap);
		const TCHAR *GetObjectName();

		SvGraphNodeReference SvTraverseAnimGraph(IGraphObjectManager *gom, Animatable *owner, int id, DWORD flags);
		TSTR SvGetRelTip(IGraphObjectManager *gom, IGraphNode *gNodeTarger, int id, IGraphNode *gNodeMaker);

		IOResult Load(ILoad *iload);
		IOResult Save(ISave *isave);

		ChannelMask ChannelsUsed();
		ChannelMask ChannelsChanged();

		void Bez3D(Point3& b, const Point3 *p, const float& u);
		void ModifyObject(TimeValue t, ModContext& mc, ObjectState *os, INode *node);
		Class_ID InputType();
	
		Interval LocalValidity(TimeValue t);
		void NotifyInputChanged(Interval changeInt, PartID partID, RefMessage message, ModContext *mc);

		void DeleteChannel(const int&);

		BOOL ChangeTopology();
		int GetParamBlockIndex(int id);

		int NumRefs();
		RefTargetHandle GetReference(int i);

	private:

		virtual void SetReference(int i, RefTargetHandle rtarg);

	public:
		
		int NumSubs();
		Animatable *SubAnim(int i);
		TSTR SubAnimName(int i);
		bool CheckMaterialDependency(void);
		bool CheckSubMaterialDependency(void);
		RefResult NotifyRefChanged(Interval changeInt,RefTargetHandle hTarget, PartID& partID, RefMessage message);
		void TestMorphReferenceDependencies(const RefTargetHandle hTarget);
		
		CreateMouseCallBack *GetCreateMouseCallBack();
		void BeginEditParams(IObjParam *ip, ULONG flags, Animatable *prev);
		void EndEditParams(IObjParam *ip, ULONG flags, Animatable *next);

		Interval GetValidity(TimeValue t);
		ParamDimension *GetParameterDim(int pbIndex);
		TSTR GetParameterName(int pbIndex);

		MorphExport void VScroll(int code, short int cpos);
		MorphExport void Clamp_chanNum();
		MorphExport void ChannelOp(int src, int targ, int flags);
		MorphExport void Update_globalParams();
		MorphExport void Update_advancedParams();	
		MorphExport void Update_channelParams();
		MorphExport float GetIncrements();
		MorphExport void Update_SpinnerIncrements();
		MorphExport void Update_colorIndicators();
		MorphExport void Update_channelNames();
		MorphExport void Update_channelValues();
		MorphExport void Update_channelLimits();
		MorphExport void Update_channelInfo();
		MorphExport void Update_channelMarkers();
		MorphExport void Update_channelFULL();

		MorphExport float TrimDown(float value, int decimalpts);

		BOOL						inRender;

		int RenderBegin(TimeValue t, ULONG flags);
		int RenderEnd(TimeValue t);

		int CurrentChannelIndex(void);
		morphChannel& CurrentChannel(void);

		float GetCurrentTargetPercent(void); 
		void SetCurrentTargetPercent(const float& fval);
	
		void DeleteTarget(void);
		void Update_TargetListBoxNames(void);
		void SwapTargets(const int way);
		void SwapTargets(const int from, const int to, const bool isundo);

		int GetRefNumber(int chanNum, int targNum);
		void DisplayMemoryUsage(void);

	public:

		void RescaleWorldUnits(float f);
};


#endif
