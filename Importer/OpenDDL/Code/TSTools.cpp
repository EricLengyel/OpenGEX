//
// This file is part of the Terathon Common Library, by Eric Lengyel.
// Copyright 1999-2022, Terathon Software LLC
//
// This software is distributed under the MIT License.
// Separate proprietary licenses are available from Terathon Software.
//


#include "TSTools.h"


using namespace Terathon;


#ifdef TERATHON_DEBUG

	#if defined(_MSC_VER) || defined(__ORBIS__) || defined(__PROSPERO__)

		void Terathon::Fatal(const char *message)
		{
			__debugbreak();
		}

	#elif defined(__GNUC__)

		extern "C"
		{
			int raise(int);
		}

		void Terathon::Fatal(const char *message)
		{
			raise(5);	// SIGTRAP
		}

	#endif

	void Terathon::Assert(bool condition, const char *message)
	{
		if (!condition)
		{
			Fatal(message);
		}
	}

#endif
