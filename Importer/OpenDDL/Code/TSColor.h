//
// This file is part of the Terathon Common Library, by Eric Lengyel.
// Copyright 1999-2025, Terathon Software LLC
//
// This software is distributed under the MIT License.
// Separate proprietary licenses are available from Terathon Software.
//


#ifndef TSColor_h
#define TSColor_h


/// \component	Math Library
/// \prefix		Math/


#include "TSHalf.h"


#define TERATHON_COLORRGB 1
#define TERATHON_COLORRGBA 1
#define TERATHON_COLOR1U 1
#define TERATHON_COLOR2U 1
#define TERATHON_COLOR4U 1
#define TERATHON_COLOR1S 1
#define TERATHON_COLOR2S 1
#define TERATHON_COLOR4S 1
#define TERATHON_COLOR4H 1


namespace Terathon
{
	class ColorRGB;
	class ColorRGBA;


	namespace Color
	{
		TERATHON_API extern const uint8 srgbLinearizationTable[256];
		TERATHON_API extern const uint8 srgbDelinearizationTable[256];
		TERATHON_API extern const float srgbFloatLinearizationTable[256];

		TERATHON_API float Linearize(float color);
		TERATHON_API float Delinearize(float color);
		TERATHON_API ColorRGB Linearize(const ColorRGB& color);
		TERATHON_API ColorRGB Delinearize(const ColorRGB& color);
		TERATHON_API ColorRGBA Linearize(const ColorRGBA& color);
		TERATHON_API ColorRGBA Delinearize(const ColorRGBA& color);
	}


	class LinearPrimary
	{
		private:

			float		value;

		public:

			inline LinearPrimary() = default;

			LinearPrimary(float v)
			{
				value = v;
			}

			LinearPrimary(int v)
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
			}

			LinearPrimary(unsigned int v)
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
			}

			LinearPrimary& operator =(float v)
			{
				value = v;
				return (*this);
			}

			void operator =(float v) volatile
			{
				value = v;
			}

			LinearPrimary& operator =(int v)
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
				return (*this);
			}

			void operator =(int v) volatile
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
			}

			LinearPrimary& operator =(unsigned int v)
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
				return (*this);
			}

			void operator =(unsigned int v) volatile
			{
				value = Color::srgbFloatLinearizationTable[uint8(v)];
			}

			LinearPrimary& operator +=(float v)
			{
				value += v;
				return (*this);
			}

			LinearPrimary& operator -=(float v)
			{
				value -= v;
				return (*this);
			}

			LinearPrimary& operator *=(float v)
			{
				value *= v;
				return (*this);
			}

			operator float&(void)
			{
				return (value);
			}

			operator const float&(void) const
			{
				return (value);
			}
	};


	class LinearAlpha
	{
		private:

			float		value;

		public:

			inline LinearAlpha() = default;

			LinearAlpha(float v)
			{
				value = v;
			}

			LinearAlpha(int v)
			{
				value = float(v) * (1.0F / 255.0F);
			}

			LinearAlpha(unsigned int v)
			{
				value = float(v) * (1.0F / 255.0F);
			}

			LinearAlpha& operator =(float v)
			{
				value = v;
				return (*this);
			}

			void operator =(float v) volatile
			{
				value = v;
			}

			LinearAlpha& operator =(int v)
			{
				value = float(v) * (1.0F / 255.0F);
				return (*this);
			}

			void operator =(int v) volatile
			{
				value = float(v) * (1.0F / 255.0F);
			}

			LinearAlpha& operator =(unsigned int v)
			{
				value = float(v) * (1.0F / 255.0F);
				return (*this);
			}

			void operator =(unsigned int v) volatile
			{
				value = float(v) * (1.0F / 255.0F);
			}

			LinearAlpha& operator +=(float v)
			{
				value += v;
				return (*this);
			}

			LinearAlpha& operator -=(float v)
			{
				value -= v;
				return (*this);
			}

			LinearAlpha& operator *=(float v)
			{
				value *= v;
				return (*this);
			}

			operator float&(void)
			{
				return (value);
			}

			operator const float&(void) const
			{
				return (value);
			}
	};


	/// \class	ColorRGB	Encapsulates a floating-point RGB color.
	///
	/// The $ColorRGB$ class encapsulates a floating-point RGB color.
	///
	/// \def	class ColorRGB
	///
	/// \data	ColorRGB
	///
	/// \ctor	ColorRGB();
	/// \ctor	ColorRGB(float r, float g, float b);
	///
	/// \desc
	/// The $ColorRGB$ class encapsulates a color having floating-point red, green, and blue
	/// components in the range [0.0,&#x202F;1.0]. An additional alpha component is provided by the
	/// $@ColorRGBA@$ class. When a $ColorRGB$ object is converted to a $@ColorRGBA@$ object,
	/// the alpha component is assumed to be 1.0.
	///
	/// The default constructor leaves the components of the color undefined. If the values
	/// $r$, $g$, and $b$ are supplied, then they are assigned to the red, green, and blue
	/// components of the color, respectively.
	///
	/// \operator	float& operator [](machine k);
	///				Returns a reference to the $k$-th component of a color.
	///				The value of $k$ must be 0, 1, or 2.
	///
	/// \operator	const float& operator [](machine k) const;
	///				Returns a constant reference to the $k$-th component of a color.
	///				The value of $k$ must be 0, 1, or 2.
	///
	/// \operator	ColorRGB& operator =(float s);
	///				Sets all three components to the value $s$.
	///
	/// \operator	ColorRGB& operator +=(const ColorRGB& c);
	///				Adds the color $c$.
	///
	/// \operator	ColorRGB& operator -=(const ColorRGB& c);
	///				Subtracts the color $c$.
	///
	/// \operator	ColorRGB& operator *=(const ColorRGB& c);
	///				Multiplies by the color $c$.
	///
	/// \operator	ColorRGB& operator *=(float s);
	///				Multiplies all three components by $s$.
	///
	/// \operator	ColorRGB& operator /=(float s);
	///				Divides all three components by $s$.
	///
	/// \action		ColorRGB operator -(const ColorRGB& c);
	///				Returns the negation of the color $c$.
	///
	/// \action		ColorRGB operator +(const ColorRGB& c1, const ColorRGB& c2);
	///				Returns the sum of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGB operator -(const ColorRGB& c1, const ColorRGB& c2);
	///				Returns the difference of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGB operator *(const ColorRGB& c1, const ColorRGB& c2);
	///				Returns the product of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGB operator *(const ColorRGB& c, float s);
	///				Returns the product of the color $c$ and the scalar $s$.
	///
	/// \action		ColorRGB operator *(float s, const ColorRGB& c);
	///				Returns the product of the color $c$ and the scalar $s$.
	///
	/// \action		ColorRGB operator /(const ColorRGB& c, float s);
	///				Returns the product of the color $c$ and the inverse of the scalar $s$.
	///
	/// \action		bool operator ==(const ColorRGB& c1, const ColorRGB& c2);
	///				Returns a boolean value indicating whether the colors $c1$ and $c2$ are equal.
	///
	/// \action		bool operator !=(const ColorRGB& c1, const ColorRGB& c2);
	///				Returns a boolean value indicating whether the colors $c1$ and $c2$ are not equal.
	///
	/// \action		float Luminance(const ColorRGB& c);
	///				Returns the luminance value of the color $c$.
	///
	/// \also	$@ColorRGBA@$


	/// \function	ColorRGB::Set		Sets all three components of a color.
	///
	/// \proto	ColorRGB& Set(float r, float g, float b);
	///
	/// \param	r	The new red component.
	/// \param	g	The new green component.
	/// \param	b	The new blue component.
	///
	/// \desc
	/// The $Set$ function sets the red, green, and blue components of a color to the values
	/// given by the $r$, $g$, and $b$ parameters, respectively.
	///
	/// The return value is a reference to the color object.


	/// \function	ColorRGB::GetLuminance		Returns the luminance of an RGB color.
	///
	/// \proto	float GetLuminance(void) const;
	///
	/// \desc
	/// The $GetLuminance$ function returns the luminance of an RGB color.


	/// \member		ColorRGB

	class ColorRGB
	{
		public:

			LinearPrimary		red;		///< The red component.
			LinearPrimary		green;		///< The green component.
			LinearPrimary		blue;		///< The blue component.

			inline ColorRGB() = default;

			ColorRGB(const ColorRGB& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
			}

			ColorRGB(float r, float g, float b)
			{
				red = r;
				green = g;
				blue = b;
			}

			ColorRGB(int r, int g, int b)
			{
				red = r;
				green = g;
				blue = b;
			}

			ColorRGB(unsigned int r, unsigned int g, unsigned int b)
			{
				red = r;
				green = g;
				blue = b;
			}

			ColorRGB& Set(float r, float g, float b)
			{
				red = r;
				green = g;
				blue = b;
				return (*this);
			}

			void Set(float r, float g, float b) volatile
			{
				red = r;
				green = g;
				blue = b;
			}

			ColorRGB& Set(int r, int g, int b)
			{
				red = r;
				green = g;
				blue = b;
				return (*this);
			}

			void Set(int r, int g, int b) volatile
			{
				red = r;
				green = g;
				blue = b;
			}

			ColorRGB& Set(unsigned int r, unsigned int g, unsigned int b)
			{
				red = r;
				green = g;
				blue = b;
				return (*this);
			}

			void Set(unsigned int r, unsigned int g, unsigned int b) volatile
			{
				red = r;
				green = g;
				blue = b;
			}

			float& operator [](machine k)
			{
				return (reinterpret_cast<float *>(this)[k]);
			}

			const float& operator [](machine k) const
			{
				return (reinterpret_cast<const float *>(this)[k]);
			}

			ColorRGB& operator =(const ColorRGB& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				return (*this);
			}

			void operator =(const ColorRGB& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
			}

			ColorRGB& operator =(float s)
			{
				red = s;
				green = s;
				blue = s;
				return (*this);
			}

			void operator =(float s) volatile
			{
				red = s;
				green = s;
				blue = s;
			}

			ColorRGB& operator +=(const ColorRGB& c)
			{
				red += c.red;
				green += c.green;
				blue += c.blue;
				return (*this);
			}

			ColorRGB& operator -=(const ColorRGB& c)
			{
				red -= c.red;
				green -= c.green;
				blue -= c.blue;
				return (*this);
			}

			ColorRGB& operator *=(const ColorRGB& c)
			{
				red *= c.red;
				green *= c.green;
				blue *= c.blue;
				return (*this);
			}

			ColorRGB& operator *=(float s)
			{
				red *= s;
				green *= s;
				blue *= s;
				return (*this);
			}

			ColorRGB& operator /=(float s)
			{
				s = 1.0F / s;
				red *= s;
				green *= s;
				blue *= s;
				return (*this);
			}

			float GetLuminance(void) const
			{
				// See FGED2, Section 5.2.3.

				return (red * 0.212639F + green * 0.715169F + blue * 0.072192F);
			}

			TERATHON_API void GetHueSat(float *hue, float *sat) const;
			TERATHON_API void SetHueSat(float hue, float sat);

			TERATHON_API ColorRGB GetBrightestColor(void) const;
			TERATHON_API uint32 GetPackedColorRGB9E5(void) const;

			TERATHON_API void GetHexString(char *string) const;
			TERATHON_API ColorRGB& SetHexString(const char *string);
	};


	inline ColorRGB operator -(const ColorRGB& c)
	{
		return (ColorRGB(-c.red, -c.green, -c.blue));
	}

	inline ColorRGB operator +(const ColorRGB& c1, const ColorRGB& c2)
	{
		return (ColorRGB(c1.red + c2.red, c1.green + c2.green, c1.blue + c2.blue));
	}

	inline ColorRGB operator -(const ColorRGB& c1, const ColorRGB& c2)
	{
		return (ColorRGB(c1.red - c2.red, c1.green - c2.green, c1.blue - c2.blue));
	}

	inline ColorRGB operator *(const ColorRGB& c1, const ColorRGB& c2)
	{
		return (ColorRGB(c1.red * c2.red, c1.green * c2.green, c1.blue * c2.blue));
	}

	inline ColorRGB operator *(const ColorRGB& c, float s)
	{
		return (ColorRGB(c.red * s, c.green * s, c.blue * s));
	}

	inline ColorRGB operator *(float s, const ColorRGB& c)
	{
		return (ColorRGB(s * c.red, s * c.green, s * c.blue));
	}

	inline ColorRGB operator /(const ColorRGB& c, float s)
	{
		s = 1.0F / s;
		return (ColorRGB(c.red * s, c.green * s, c.blue * s));
	}

	inline bool operator ==(const ColorRGB& c1, const ColorRGB& c2)
	{
		return ((c1.red == c2.red) && (c1.green == c2.green) && (c1.blue == c2.blue));
	}

	inline bool operator !=(const ColorRGB& c1, const ColorRGB& c2)
	{
		return ((c1.red != c2.red) || (c1.green != c2.green) || (c1.blue != c2.blue));
	}


	/// \class	ColorRGBA	Encapsulates a floating-point RGBA color.
	///
	/// The $ColorRGBA$ class encapsulates a floating-point RGBA color.
	///
	/// \def	class ColorRGBA : public ColorRGB
	///
	/// \data	ColorRGBA
	///
	/// \ctor	ColorRGBA();
	/// \ctor	ColorRGBA(const ColorRGB& c, float a = 1.0F);
	/// \ctor	ColorRGBA(float r, float g, float b, float a = 1.0F);
	///
	/// \desc
	/// The $ColorRGBA$ class encapsulates a color having floating-point red, green, blue, and
	/// alpha components in the range [0.0,&#x202F;1.0]. When a $@ColorRGB@$ object is converted
	/// to a $ColorRGBA$ object, the alpha component is assumed to be 1.0.
	///
	/// The default constructor leaves the components of the color undefined. If the values
	/// $r$, $g$, $b$, and $a$ are supplied, then they are assigned to the red, green, blue,
	/// and alpha components of the color, respectively.
	///
	/// \operator	ColorRGBA& operator =(const ColorRGB& c);
	///				Copies the red, green, and blue components of $c$, and assigns
	///				the alpha component a value of 1.
	///
	/// \operator	ColorRGBA& operator =(float s);
	///				Assigns the value $s$ to the red, green, and blue components, and
	///				assigns the alpha component a value of 1.
	///
	/// \operator	ColorRGBA& operator +=(const ColorRGBA& c);
	///				Adds the color $c$.
	///
	/// \operator	ColorRGBA& operator +=(const ColorRGB& c);
	///				Adds the color $c$. The alpha component is not modified.
	///
	/// \operator	ColorRGBA& operator -=(const ColorRGBA& c);
	///				Subtracts the color $c$.
	///
	/// \operator	ColorRGBA& operator -=(const ColorRGB& c);
	///				Subtracts the color $c$. The alpha component is not modified.
	///
	/// \operator	ColorRGBA& operator *=(const ColorRGBA& c);
	///				Multiplies by the color $c$.
	///
	/// \operator	ColorRGBA& operator *=(const ColorRGB& c);
	///				Multiplies by the color $c$. The alpha component is not modified.
	///
	/// \operator	ColorRGBA& operator *=(float s);
	///				Multiplies all four components by $s$.
	///
	/// \operator	ColorRGBA& operator /=(float s);
	///				Divides all four components by $s$.
	///
	/// \action		ColorRGBA operator -(const ColorRGBA& c);
	///				Returns the negation of the color $c$.
	///
	/// \action		ColorRGBA operator +(const ColorRGBA& c1, const ColorRGBA& c2);
	///				Returns the sum of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGBA operator +(const ColorRGBA& c1, const ColorRGB& c2);
	///				Returns the sum of the colors $c1$ and $c2$. The alpha component of $c2$ is assumed to be 0.
	///
	/// \action		ColorRGBA operator -(const ColorRGBA& c1, const ColorRGBA& c2);
	///				Returns the difference of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGBA operator -(const ColorRGBA& c1, const ColorRGB& c2);
	///				Returns the difference of the colors $c1$ and $c2$. The alpha component of $c2$ is assumed to be 0.
	///
	/// \action		ColorRGBA operator *(const ColorRGBA& c1, const ColorRGBA& c2);
	///				Returns the product of the colors $c1$ and $c2$.
	///
	/// \action		ColorRGBA operator *(const ColorRGBA& c1, const ColorRGB& c2);
	///				Returns the product of the colors $c1$ and $c2$. The alpha component of $c2$ is assumed to be 1.
	///
	/// \action		ColorRGBA operator *(const ColorRGB& c1, const ColorRGBA& c2);
	///				Returns the product of the colors $c1$ and $c2$. The alpha component of $c1$ is assumed to be 1.
	///
	/// \action		ColorRGBA operator *(const ColorRGBA& c, float s);
	///				Returns the product of the color $c$ and the scalar $s$.
	///
	/// \action		ColorRGBA operator *(float s, const ColorRGBA& c);
	///				Returns the product of the color $c$ and the scalar $s$.
	///
	/// \action		ColorRGBA operator /(const ColorRGBA& c, float s);
	///				Returns the product of the color $c$ and the inverse of the scalar $s$.
	///
	/// \action		bool operator ==(const ColorRGBA& c1, const ColorRGBA& c2);
	///				Returns a boolean value indicating whether the two colors $c1$ and $c2$ are equal.
	///
	/// \action		bool operator !=(const ColorRGBA& c1, const ColorRGBA& c2);
	///				Returns a boolean value indicating whether the two colors $c1$ and $c2$ are not equal.
	///
	/// \base	$@ColorRGB@$


	/// \function	ColorRGBA::Set		Sets all four components of a color.
	///
	/// \proto	ColorRGBA& Set(float r, float g, float b, float a = 1.0F);
	///
	/// \param	r	The new red component.
	/// \param	g	The new green component.
	/// \param	b	The new blue component.
	/// \param	a	The new alpha component.
	///
	/// \desc
	/// The $Set$ function sets the red, green, blue, and alpha components of a color to the values
	/// given by the $r$, $g$, $b$, and $a$ parameters, respectively.
	///
	/// The return value is a reference to the color object.


	/// \function	ColorRGBA::GetColorRGB		Returns a reference to a $@ColorRGB@$ object.
	///
	/// \proto	ColorRGB& GetColorRGB(void);
	/// \proto	const ColorRGB& GetColorRGB(void) const;
	///
	/// \desc
	/// The $GetColorRGB$ function returns a reference to the $@ColorRGB@$ base class object of the $ColorRGBA$ object.
	/// This conversion can be done implicitly in most situations without calling the $GetColorRGB$ function.


	/// \member		ColorRGBA

	class ColorRGBA : public ColorRGB
	{
		public:

			LinearAlpha			alpha;		///< The alpha component.

			inline ColorRGBA() = default;

			ColorRGBA(const ColorRGBA& c) : ColorRGB(c)
			{
				alpha = c.alpha;
			}

			ColorRGBA(const ColorRGB& c, float a = 1.0F) : ColorRGB(c)
			{
				alpha = a;
			}

			ColorRGBA(float r, float g, float b, float a = 1.0F) : ColorRGB(r, g, b)
			{
				alpha = a;
			}

			ColorRGBA(int r, int g, int b, int a = 255) : ColorRGB(r, g, b)
			{
				alpha = a;
			}

			ColorRGBA(unsigned int r, unsigned int g, unsigned int b, unsigned int a = 255U) : ColorRGB(r, g, b)
			{
				alpha = a;
			}

			ColorRGBA& Set(const ColorRGB& c, float a)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = a;
				return (*this);
			}

			void Set(const ColorRGB& c, float a) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = a;
			}

			ColorRGBA& Set(float r, float g, float b, float a = 1.0F)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void Set(float r, float g, float b, float a = 1.0F) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			ColorRGBA& Set(int r, int g, int b, int a = 255)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void Set(int r, int g, int b, int a = 255) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			ColorRGBA& Set(unsigned int r, unsigned int g, unsigned int b, unsigned int a = 255U)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void Set(unsigned int r, unsigned int g, unsigned int b, unsigned int a = 255U) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			ColorRGBA& SetLinear(uint8 r, uint8 g, uint8 b, uint8 a = 255U)
			{
				red = float(r) * (1.0F / 255.0F);
				green = float(g) * (1.0F / 255.0F);
				blue = float(b) * (1.0F / 255.0F);
				alpha = float(a) * (1.0F / 255.0F);
				return (*this);
			}

			void SetLinear(uint8 r, uint8 g, uint8 b, uint8 a = 255U) volatile
			{
				red = float(r) * (1.0F / 255.0F);
				green = float(g) * (1.0F / 255.0F);
				blue = float(b) * (1.0F / 255.0F);
				alpha = float(a) * (1.0F / 255.0F);
			}

			ColorRGBA& SetLinear(float r, float g, float b, float a = 1.0F)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void SetLinear(float r, float g, float b, float a = 1.0F) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			ColorRGBA& SetLinear(const ColorRGBA& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
				return (*this);
			}

			void SetLinear(const ColorRGBA& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			ColorRGB& GetColorRGB(void)
			{
				return (*this);
			}

			const ColorRGB& GetColorRGB(void) const
			{
				return (*this);
			}

			ColorRGBA& operator =(const ColorRGBA& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
				return (*this);
			}

			void operator =(const ColorRGBA& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			ColorRGBA& operator =(const ColorRGB& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = 1.0F;
				return (*this);
			}

			void operator =(const ColorRGB& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = 1.0F;
			}

			ColorRGBA& operator =(float s)
			{
				red = s;
				green = s;
				blue = s;
				alpha = 1.0F;
				return (*this);
			}

			void operator =(float s) volatile
			{
				red = s;
				green = s;
				blue = s;
				alpha = 1.0F;
			}

			ColorRGBA& operator +=(const ColorRGBA& c)
			{
				red += c.red;
				green += c.green;
				blue += c.blue;
				alpha += c.alpha;
				return (*this);
			}

			ColorRGBA& operator +=(const ColorRGB& c)
			{
				red += c.red;
				green += c.green;
				blue += c.blue;
				return (*this);
			}

			ColorRGBA& operator -=(const ColorRGBA& c)
			{
				red -= c.red;
				green -= c.green;
				blue -= c.blue;
				alpha -= c.alpha;
				return (*this);
			}

			ColorRGBA& operator -=(const ColorRGB& c)
			{
				red -= c.red;
				green -= c.green;
				blue -= c.blue;
				return (*this);
			}

			ColorRGBA& operator *=(const ColorRGBA& c)
			{
				red *= c.red;
				green *= c.green;
				blue *= c.blue;
				alpha *= c.alpha;
				return (*this);
			}

			ColorRGBA& operator *=(const ColorRGB& c)
			{
				red *= c.red;
				green *= c.green;
				blue *= c.blue;
				return (*this);
			}

			ColorRGBA& operator *=(float s)
			{
				red *= s;
				green *= s;
				blue *= s;
				alpha *= s;
				return (*this);
			}

			ColorRGBA& operator /=(float s)
			{
				s = 1.0F / s;
				red *= s;
				green *= s;
				blue *= s;
				alpha *= s;
				return (*this);
			}

			TERATHON_API void GetHexString(char *string) const;
			TERATHON_API ColorRGBA& SetHexString(const char *string);
	};


	inline ColorRGBA operator -(const ColorRGBA& c)
	{
		return (ColorRGBA(-c.red, -c.green, -c.blue, -c.alpha));
	}

	inline ColorRGBA operator +(const ColorRGBA& c1, const ColorRGBA& c2)
	{
		return (ColorRGBA(c1.red + c2.red, c1.green + c2.green, c1.blue + c2.blue, c1.alpha + c2.alpha));
	}

	inline ColorRGBA operator +(const ColorRGBA& c1, const ColorRGB& c2)
	{
		return (ColorRGBA(c1.red + c2.red, c1.green + c2.green, c1.blue + c2.blue, c1.alpha));
	}

	inline ColorRGBA operator -(const ColorRGBA& c1, const ColorRGBA& c2)
	{
		return (ColorRGBA(c1.red - c2.red, c1.green - c2.green, c1.blue - c2.blue, c1.alpha - c2.alpha));
	}

	inline ColorRGBA operator -(const ColorRGBA& c1, const ColorRGB& c2)
	{
		return (ColorRGBA(c1.red - c2.red, c1.green - c2.green, c1.blue - c2.blue, c1.alpha));
	}

	inline ColorRGBA operator *(const ColorRGBA& c1, const ColorRGBA& c2)
	{
		return (ColorRGBA(c1.red * c2.red, c1.green * c2.green, c1.blue * c2.blue, c1.alpha * c2.alpha));
	}

	inline ColorRGBA operator *(const ColorRGBA& c1, const ColorRGB& c2)
	{
		return (ColorRGBA(c1.red * c2.red, c1.green * c2.green, c1.blue * c2.blue, c1.alpha));
	}

	inline ColorRGBA operator *(const ColorRGB& c1, const ColorRGBA& c2)
	{
		return (ColorRGBA(c1.red * c2.red, c1.green * c2.green, c1.blue * c2.blue, c2.alpha));
	}

	inline ColorRGBA operator *(const ColorRGBA& c, float s)
	{
		return (ColorRGBA(c.red * s, c.green * s, c.blue * s, c.alpha * s));
	}

	inline ColorRGBA operator *(float s, const ColorRGBA& c)
	{
		return (ColorRGBA(s * c.red, s * c.green, s * c.blue, s * c.alpha));
	}

	inline ColorRGBA operator /(const ColorRGBA& c, float s)
	{
		s = 1.0F / s;
		return (ColorRGBA(c.red * s, c.green * s, c.blue * s, c.alpha * s));
	}

	inline bool operator ==(const ColorRGBA& c1, const ColorRGBA& c2)
	{
		return ((c1.red == c2.red) && (c1.green == c2.green) && (c1.blue == c2.blue) && (c1.alpha == c2.alpha));
	}

	inline bool operator !=(const ColorRGBA& c1, const ColorRGBA& c2)
	{
		return ((c1.red != c2.red) || (c1.green != c2.green) || (c1.blue != c2.blue) || (c1.alpha != c2.alpha));
	}

	inline float Luminance(const ColorRGBA& c)
	{
		return (c.red * 0.212639F + c.green * 0.715169F + c.blue * 0.072192F);
	}


	struct ConstColorRGB
	{
		float		red;
		float		green;
		float		blue;

		operator const ColorRGB&(void) const
		{
			return (reinterpret_cast<const ColorRGB&>(*this));
		}

		const ColorRGB *operator &(void) const
		{
			return (reinterpret_cast<const ColorRGB *>(this));
		}

		const ColorRGB *operator ->(void) const
		{
			return (reinterpret_cast<const ColorRGB *>(this));
		}
	};


	struct ConstColorRGBA
	{
		float		red;
		float		green;
		float		blue;
		float		alpha;

		operator const ColorRGBA&(void) const
		{
			return (reinterpret_cast<const ColorRGBA&>(*this));
		}

		const ColorRGBA *operator &(void) const
		{
			return (reinterpret_cast<const ColorRGBA *>(this));
		}

		const ColorRGBA *operator ->(void) const
		{
			return (reinterpret_cast<const ColorRGBA *>(this));
		}
	};


	inline bool operator ==(const ColorRGB& c1, const ConstColorRGB& c2)
	{
		return ((c1.red == c2.red) && (c1.green == c2.green) && (c1.blue == c2.blue));
	}

	inline bool operator !=(const ColorRGB& c1, const ConstColorRGB& c2)
	{
		return ((c1.red != c2.red) || (c1.green != c2.green) || (c1.blue != c2.blue));
	}

	inline bool operator ==(const ColorRGBA& c1, const ConstColorRGBA& c2)
	{
		return ((c1.red == c2.red) && (c1.green == c2.green) && (c1.blue == c2.blue) && (c1.alpha == c2.alpha));
	}

	inline bool operator !=(const ColorRGBA& c1, const ConstColorRGBA& c2)
	{
		return ((c1.red != c2.red) || (c1.green != c2.green) || (c1.blue != c2.blue) || (c1.alpha != c2.alpha));
	}


	typedef uint8	Color1U;
	typedef int8	Color1S;


	/// \class	Color2U		Encapsulates a two-component unsigned integer color.
	///
	/// The $Color2U$ class encapsulates a two-component unsigned integer color.
	///
	/// \def	class Color2U
	///
	/// \ctor	Color2U();
	/// \ctor	Color2U(uint32 r, uint32 g);
	///
	/// \desc
	/// The $Color2U$ class encapsulates a color having two unsigned integer
	/// components in the range [0,&#x202F;255].
	///
	/// The default constructor leaves the components of the color undefined.
	///
	/// \also	$@Color2S@$
	/// \also	$@Color4U@$
	/// \also	$@Color4S@$


	class Color2U
	{
		public:

			uint8		red;
			uint8		green;

			inline Color2U() = default;

			Color2U(uint32 r, uint32 g)
			{
				red = uint8(r);
				green = uint8(g);
			}

			Color2U& Set(uint32 r, uint32 g)
			{
				red = uint8(r);
				green = uint8(g);
				return (*this);
			}

			Color2U& Clear(void)
			{
				reinterpret_cast<uint16&>(*this) = 0;
				return (*this);
			}

			uint16 GetPackedColor(void) const
			{
				return (reinterpret_cast<const uint16&>(*this));
			}

			Color2U& SetPackedColor(uint16 c)
			{
				reinterpret_cast<uint16&>(*this) = c;
				return (*this);
			}

			void SetPackedColor(uint16 c) volatile
			{
				reinterpret_cast<volatile uint16&>(*this) = c;
			}

			Color2U& operator =(const Color2U& c)
			{
				reinterpret_cast<uint16&>(*this) = c.GetPackedColor();
				return (*this);
			}

			void operator =(const Color2U& c) volatile
			{
				reinterpret_cast<volatile uint16&>(*this) = c.GetPackedColor();
			}

			bool operator ==(const Color2U& c) const
			{
				return (GetPackedColor() == c.GetPackedColor());
			}

			bool operator !=(const Color2U& c) const
			{
				return (GetPackedColor() != c.GetPackedColor());
			}
	};


	/// \class	Color2S		Encapsulates a two-component signed integer color.
	///
	/// The $Color2S$ class encapsulates a two-component signed integer color.
	///
	/// \def	class Color2S
	///
	/// \ctor	Color2S();
	/// \ctor	Color2S(int32 r, int32 g);
	///
	/// \desc
	/// The $Color2S$ class encapsulates a color having two signed integer
	/// components in the range [&minus;127,&#x202F;+127].
	///
	/// The default constructor leaves the components of the color undefined.
	///
	/// \also	$@Color2U@$
	/// \also	$@Color4S@$
	/// \also	$@Color4U@$


	class Color2S
	{
		public:

			int8		red;
			int8		green;

			inline Color2S() = default;

			Color2S(int32 r, int32 g)
			{
				red = int8(r);
				green = int8(g);
			}

			Color2S& Set(int32 r, int32 g)
			{
				red = int8(r);
				green = int8(g);
				return (*this);
			}

			Color2S& Clear(void)
			{
				reinterpret_cast<int16&>(*this) = 0;
				return (*this);
			}

			uint16 GetPackedColor(void) const
			{
				return (reinterpret_cast<const uint16&>(*this));
			}

			Color2S& SetPackedColor(uint16 c)
			{
				reinterpret_cast<uint16&>(*this) = c;
				return (*this);
			}

			void SetPackedColor(uint16 c) volatile
			{
				reinterpret_cast<volatile uint16&>(*this) = c;
			}

			Color2S& operator =(const Color2S& c)
			{
				reinterpret_cast<uint16&>(*this) = c.GetPackedColor();
				return (*this);
			}

			void operator =(const Color2S& c) volatile
			{
				reinterpret_cast<volatile uint16&>(*this) = c.GetPackedColor();
			}

			bool operator ==(const Color2S& c) const
			{
				return (GetPackedColor() == c.GetPackedColor());
			}

			bool operator !=(const Color2S& c) const
			{
				return (GetPackedColor() != c.GetPackedColor());
			}
	};


	/// \class	Color4U		Encapsulates a four-component unsigned integer color.
	///
	/// The $Color4U$ class encapsulates a four-component unsigned integer color.
	///
	/// \def	class Color4U
	///
	/// \ctor	Color4U();
	/// \ctor	Color4U(uint32 r, uint32 g, uint32 b, uint32 a = 255U);
	/// \ctor	explicit Color4U(const ColorRGBA& c);
	///
	/// \desc
	/// The $Color4U$ class encapsulates a color having unsigned integer red, green, blue, and alpha
	/// components in the range [0,&#x202F;255].
	///
	/// The default constructor leaves the components of the color undefined.
	///
	/// \also	$@Color4S@$
	/// \also	$@Color2U@$
	/// \also	$@Color2S@$


	class Color4U
	{
		public:

			uint8		red;
			uint8		green;
			uint8		blue;
			uint8		alpha;

			inline Color4U() = default;

			Color4U(uint32 r, uint32 g, uint32 b, uint32 a = 255U)
			{
				red = uint8(r);
				green = uint8(g);
				blue = uint8(b);
				alpha = uint8(a);
			}

			explicit Color4U(const ColorRGBA& c)
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
			}

			Color4U& Set(uint32 r, uint32 g, uint32 b, uint32 a = 255U)
			{
				red = uint8(r);
				green = uint8(g);
				blue = uint8(b);
				alpha = uint8(a);
				return (*this);
			}

			void Set(uint32 r, uint32 g, uint32 b, uint32 a = 255U) volatile
			{
				red = uint8(r);
				green = uint8(g);
				blue = uint8(b);
				alpha = uint8(a);
			}

			Color4U& SetLinear(uint8 r, uint8 g, uint8 b, uint8 a = 255U)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void SetLinear(uint8 r, uint8 g, uint8 b, uint8 a = 255U) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			Color4U& SetLinear(float r, float g, float b, float a = 1.0F)
			{
				red = uint8(r * 255.0F + 0.5F);
				green = uint8(g * 255.0F + 0.5F);
				blue = uint8(b * 255.0F + 0.5F);
				alpha = uint8(a * 255.0F + 0.5F);
				return (*this);
			}

			void SetLinear(float r, float g, float b, float a = 1.0F) volatile
			{
				red = uint8(r * 255.0F + 0.5F);
				green = uint8(g * 255.0F + 0.5F);
				blue = uint8(b * 255.0F + 0.5F);
				alpha = uint8(a * 255.0F + 0.5F);
			}

			Color4U& Set(const ColorRGB& c, uint32 a = 255U)
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = a;
				return (*this);
			}

			void Set(const ColorRGB& c, uint32 a = 255U) volatile
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = a;
			}

			Color4U& Set(const ColorRGBA& c)
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
				return (*this);
			}

			void Set(const ColorRGBA& c) volatile
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
			}

			Color4U& SetLinear(const ColorRGBA& c)
			{
				red = uint8(c.red * 255.0F + 0.5F);
				green = uint8(c.green * 255.0F + 0.5F);
				blue = uint8(c.blue * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
				return (*this);
			}

			void SetLinear(const ColorRGBA& c) volatile
			{
				red = uint8(c.red * 255.0F + 0.5F);
				green = uint8(c.green * 255.0F + 0.5F);
				blue = uint8(c.blue * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
			}

			Color4U& Clear(void)
			{
				reinterpret_cast<uint32&>(*this) = 0;
				return (*this);
			}

			Color4U& ClearMaxAlpha(void)
			{
				reinterpret_cast<uint32&>(*this) = 0xFF000000;
				return (*this);
			}

			uint32 GetPackedColor(void) const
			{
				return (reinterpret_cast<const uint32&>(*this));
			}

			Color4U& SetPackedColor(uint32 c)
			{
				reinterpret_cast<uint32&>(*this) = c;
				return (*this);
			}

			void SetPackedColor(uint32 c) volatile
			{
				reinterpret_cast<volatile uint32&>(*this) = c;
			}

			explicit operator ColorRGBA(void) const
			{
				return (ColorRGBA(red, green, blue, alpha));
			}

			Color4U& operator =(const Color4U& c)
			{
				reinterpret_cast<uint32&>(*this) = c.GetPackedColor();
				return (*this);
			}

			void operator =(const Color4U& c) volatile
			{
				reinterpret_cast<volatile uint32&>(*this) = c.GetPackedColor();
			}

			Color4U& operator =(const ColorRGB& c)
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = 255U;
				return (*this);
			}

			void operator =(const ColorRGB& c) volatile
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = 255U;
			}

			Color4U& operator =(const ColorRGBA& c)
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
				return (*this);
			}

			void operator =(const ColorRGBA& c) volatile
			{
				red = uint8(Color::Delinearize(c.red) * 255.0F + 0.5F);
				green = uint8(Color::Delinearize(c.green) * 255.0F + 0.5F);
				blue = uint8(Color::Delinearize(c.blue) * 255.0F + 0.5F);
				alpha = uint8(c.alpha * 255.0F + 0.5F);
			}

			bool operator ==(const Color4U& c) const
			{
				return (GetPackedColor() == c.GetPackedColor());
			}

			bool operator !=(const Color4U& c) const
			{
				return (GetPackedColor() != c.GetPackedColor());
			}
	};


	/// \class	Color4S		Encapsulates a four-component signed integer color.
	///
	/// The $Color4S$ class encapsulates a four-component signed integer color.
	///
	/// \def	class Color4S
	///
	/// \ctor	Color4S();
	/// \ctor	Color4S(int32 r, int32 g, int32 b, int32 a = 0);
	///
	/// \desc
	/// The $Color4S$ class encapsulates a color having signed integer red, green, blue, and alpha
	/// components in the range [&minus;127,&#x202F;+127].
	///
	/// The default constructor leaves the components of the color undefined.
	///
	/// \also	$@Color4U@$
	/// \also	$@Color2S@$
	/// \also	$@Color2U@$


	class Color4S
	{
		public:

			int8		red;
			int8		green;
			int8		blue;
			int8		alpha;

			inline Color4S() = default;

			Color4S(int32 r, int32 g, int32 b, int32 a = 0)
			{
				red = int8(r);
				green = int8(g);
				blue = int8(b);
				alpha = int8(a);
			}

			Color4S& Set(int32 r, int32 g, int32 b, int32 a = 0)
			{
				red = int8(r);
				green = int8(g);
				blue = int8(b);
				alpha = int8(a);
				return (*this);
			}

			void Set(int32 r, int32 g, int32 b, int32 a = 0) volatile
			{
				red = int8(r);
				green = int8(g);
				blue = int8(b);
				alpha = int8(a);
			}

			Color4S& Clear(void)
			{
				reinterpret_cast<uint32&>(*this) = 0;
				return (*this);
			}

			uint32 GetPackedColor(void) const
			{
				return (reinterpret_cast<const uint32&>(*this));
			}

			Color4S& SetPackedColor(uint32 c)
			{
				reinterpret_cast<uint32&>(*this) = c;
				return (*this);
			}

			void SetPackedColor(uint32 c) volatile
			{
				reinterpret_cast<volatile uint32&>(*this) = c;
			}

			Color4S& operator =(const Color4S& c)
			{
				reinterpret_cast<uint32&>(*this) = c.GetPackedColor();
				return (*this);
			}

			void operator =(const Color4S& c) volatile
			{
				reinterpret_cast<volatile uint32&>(*this) = c.GetPackedColor();
			}

			bool operator ==(const Color4S& c) const
			{
				return (GetPackedColor() == c.GetPackedColor());
			}

			bool operator !=(const Color4S& c) const
			{
				return (GetPackedColor() != c.GetPackedColor());
			}
	};


	struct ConstColor4U
	{
		uint8		red;
		uint8		green;
		uint8		blue;
		uint8		alpha;

		operator const Color4U&(void) const
		{
			return (reinterpret_cast<const Color4U&>(*this));
		}

		const Color4U *operator &(void) const
		{
			return (reinterpret_cast<const Color4U *>(this));
		}

		const Color4U *operator ->(void) const
		{
			return (reinterpret_cast<const Color4U *>(this));
		}
	};


	class Color4H
	{
		public:

			Half		red;
			Half		green;
			Half		blue;
			Half		alpha;

			inline Color4H() = default;

			Color4H(float r, float g, float b, float a = 0.0F)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			explicit Color4H(const ColorRGBA& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			Color4H& Set(float r, float g, float b, float a = 0.0F)
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
				return (*this);
			}

			void Set(float r, float g, float b, float a = 0.0F) volatile
			{
				red = r;
				green = g;
				blue = b;
				alpha = a;
			}

			Color4H& Set(const ColorRGBA& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
				return (*this);
			}

			void Set(const ColorRGBA& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			Color4H& operator =(const Color4H& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
				return (*this);
			}

			void operator =(const Color4H& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			Color4H& operator =(const ColorRGBA& c)
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
				return (*this);
			}

			void operator =(const ColorRGBA& c) volatile
			{
				red = c.red;
				green = c.green;
				blue = c.blue;
				alpha = c.alpha;
			}

			bool operator ==(const Color4H& c) const
			{
				return ((red == c.red) && (green == c.green) && (blue == c.blue) && (alpha == c.alpha));
			}

			bool operator !=(const Color4H& c) const
			{
				return ((red != c.red) || (green != c.green) || (blue != c.blue) || (alpha != c.alpha));
			}
	};


	namespace Color
	{
		TERATHON_API extern const ConstColorRGBA black;
		TERATHON_API extern const ConstColorRGBA white;
		TERATHON_API extern const ConstColorRGBA transparent;
		TERATHON_API extern const ConstColorRGBA red;
		TERATHON_API extern const ConstColorRGBA green;
		TERATHON_API extern const ConstColorRGBA blue;
		TERATHON_API extern const ConstColorRGBA yellow;
		TERATHON_API extern const ConstColorRGBA cyan;
		TERATHON_API extern const ConstColorRGBA magenta;
	}
}


#endif
