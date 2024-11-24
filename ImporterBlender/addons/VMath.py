import sys
import math

class Vector2D:
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
	
	def __init__(self, x, y):
		self.x = x
		self.y = y


class Vector3D:
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0

	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z


class Vector4D:
	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.z = 0.0
		self.w = 0.0

	def __init__(self, x, y, z, w):
		self.x = x
		self.y = y
		self.z = z
		self.w = w

	def __init__(self, vector3, w):
		self.x = vector3.x
		self.y = vector3.y
		self.z = vector3.z
		self.w = w

	def __mul__(self, v):
		self.x *= v.x
		self.y *= v.y
		self.z *= v.z
		self.w *= v.w

class Qtrn:
	def __init__(self, w, x, y, z):
		self.w = w
		self.x = x
		self.y = y
		self.z = z

	def __mul__(self, q):
		temp_w = self.w * q.w - self.x * q.x - self.y * q.y - self.z * q.z
		temp_x = self.w * q.x + self.x * q.w + self.y * q.z - self.z * q.y
		temp_y = self.w * q.y + self.y * q.w + self.z * q.x - self.x * q.z
		temp_z = self.w * q.z + self.z * q.w + self.x * q.y - self.y * q.x

		self.w = temp_w
		self.x = temp_x
		self.y = temp_y
		self.z = temp_z

	def get_Matrix4(self):
		matrix = Matrix4D()
		matrix.set_identity()
			
		sqw = self.w * self.w
		sqx = self.x * self.x
		sqy = self.y * self.y
		sqz = self.z * self.z
		
		# invs (inverse square length) is only required if quaternion is not already normalised
		invs = 1 / (sqx + sqy + sqz + sqw)
		matrix.m00 = ( sqx - sqy - sqz + sqw) * invs # since sqw + sqx + sqy + sqz =1/invs*invs
		matrix.m11 = (-sqx + sqy - sqz + sqw) * invs
		matrix.m22 = (-sqx - sqy + sqz + sqw) * invs
		
		matrix.m10 = 2.0 * (self.x * self.y + self.z * self.w) * invs
		matrix.m01 = 2.0 * (self.x * self.y - self.z * self.w) * invs
		
		matrix.m20 = 2.0 * (self.x * self.z - self.y * self.w) * invs
		matrix.m02 = 2.0 * (self.x * self.z + self.y * self.w) * invs
		
		matrix.m21 = 2.0 * (self.y * self.z + self.x * self.w) * invs
		matrix.m12 = 2.0 * (self.y * self.z - self.x * self.w) * invs
		
		return matrix


class Matrix2D:
	def __init__(self, m00, m01, m10, m11):
		self.m00 = m00
		self.m01 = m01
		self.m10 = m10
		self.m11 = m11

	def set_identity(self):
		self.m00 = 1.0
		self.m01 = 0.0
		self.m10 = 1.0
		self.m11 = 0.0


class Matrix3D:
	def __init__(self):
		self.m00 = 0.0
		self.m01 = 0.0
		self.m02 = 0.0
		self.m10 = 0.0
		self.m11 = 0.0
		self.m12 = 0.0
		self.m20 = 0.0
		self.m21 = 0.0
		self.m22 = 0.0

	def set(self, matrix):
		self.m00 = matrix.m00
		self.m01 = matrix.m01
		self.m02 = matrix.m02
		self.m10 = matrix.m10
		self.m11 = matrix.m11
		self.m12 = matrix.m12
		self.m20 = matrix.m0
		self.m21 = matrix.m1
		self.m22 = matrix.m2

	def set_all(self, m00, m01, m02, m10, m11, m12, m20, m21, m22):
		self.m00 = m00
		self.m01 = m01
		self.m02 = m02
		self.m10 = m10
		self.m11 = m11
		self.m12 = m12
		self.m20 = m20
		self.m21 = m21
		self.m22 = m22

	def set_identity(self):
		self.m00 = 1.0
		self.m01 = 0.0
		self.m02 = 0.0
		self.m10 = 0.0
		self.m11 = 1.0
		self.m12 = 0.0
		self.m20 = 0.0
		self.m21 = 0.0
		self.m22 = 1.0

	def __mul__(self, m):
		matrix = Matrix3D()
		matrix.set_all(self.m00 * m.m00 + self.m01 * m.m10 + self.m02 * m.m20,
					self.m00 * m.m01 + self.m01 * m.m11 + self.m02 * m.m21,
					self.m00 * m.m02 + self.m01 * m.m12 + self.m02 * m.m22,
					self.m10 * m.m00 + self.m11 * m.m10 + self.m12 * m.m20, 
					self.m10 * m.m01 + self.m11 * m.m11 + self.m12 * m.m21,
					self.m10 * m.m02 + self.m11 * m.m12 + self.m12 * m.m22,
					self.m20 * m.m00 + self.m21 * m.m10 + self.m22 * m.m20, 
					self.m20 * m.m01 + self.m21 * m.m11 + self.m22 * m.m21,
					self.m20 * m.m02 + self.m21 * m.m12 + self.m22 * m.m22)
		return matrix
	
	def transpose(self):
		matrix = Matrix3D()
		matrix.set_all(self.m00, self.m10, self.m20, self.m01, self.m11, self.m21, self.m02, self.m12, self.m22)
		
		return matrix


class Matrix4D:
	def __init__(self):
		self.m00 = 0.0
		self.m01 = 0.0
		self.m02 = 0.0
		self.m03 = 0.0
		self.m10 = 0.0
		self.m11 = 0.0
		self.m12 = 0.0
		self.m13 = 0.0
		self.m20 = 0.0
		self.m21 = 0.0
		self.m22 = 0.0
		self.m23 = 0.0
		self.m30 = 0.0
		self.m31 = 0.0
		self.m32 = 0.0
		self.m33 = 0.0

	def set(self, matrix):
		self.m00 = matrix.m00
		self.m01 = matrix.m01
		self.m02 = matrix.m02
		self.m03 = matrix.m03
		self.m10 = matrix.m10
		self.m11 = matrix.m11
		self.m12 = matrix.m12
		self.m13 = matrix.m13
		self.m20 = matrix.m20
		self.m21 = matrix.m21
		self.m22 = matrix.m22
		self.m23 = matrix.m23
		self.m30 = matrix.m30
		self.m31 = matrix.m31
		self.m32 = matrix.m32
		self.m33 = matrix.m33

	def set_all(self, m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23, m30, m31, m32, m33):
		self.m00 = m00
		self.m01 = m01
		self.m02 = m02
		self.m03 = m03
		self.m10 = m10
		self.m11 = m11
		self.m12 = m12
		self.m13 = m13
		self.m20 = m20
		self.m21 = m21
		self.m22 = m22
		self.m23 = m23
		self.m30 = m30
		self.m31 = m31
		self.m32 = m32
		self.m33 = m33

	def set_most(self, m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23):
		self.m00 = m00
		self.m01 = m01
		self.m02 = m02
		self.m03 = m03
		self.m10 = m10
		self.m11 = m11
		self.m12 = m12
		self.m13 = m13
		self.m20 = m20
		self.m21 = m21
		self.m22 = m22
		self.m23 = m23
		self.m30 = 0.0
		self.m31 = 0.0
		self.m32 = 0.0
		self.m33 = 1.0

	def set_identity(self):
		self.m00 = 1.0
		self.m01 = 0.0
		self.m02 = 0.0
		self.m03 = 0.0
		self.m10 = 0.0
		self.m11 = 1.0
		self.m12 = 0.0
		self.m13 = 0.0
		self.m20 = 0.0
		self.m21 = 0.0
		self.m22 = 1.0
		self.m23 = 0.0
		self.m30 = 0.0
		self.m31 = 0.0
		self.m32 = 0.0
		self.m33 = 1.0

	def set_translation(self, vector):
		self.m03 = vector.x
		self.m13 = vector.y
		self.m23 = vector.z

	def set_translation(self, x, y, z):
		self.m03 = x
		self.m13 = y
		self.m23 = z

	def set_rotation(self, angle, vector):
		c = math.cos(angle)
		s = math.sin(angle)
		axis = normalize(vector)
		temp = (1 - c) * axis

		self.m00 = c + temp.x * axis.x
		self.m01 = 0 + temp.x * axis.y + s * axis.z
		self.m02 = 0 + temp.x * axis.z - s * axis.y
		
		self.m10 = 0 + temp.y * axis.x - s * axis.z
		self.m11 = c + temp.y * axis.y
		self.m12 = 0 + temp.y * axis.z + s * axis.x
		
		self.m20 = 0 + temp.z * axis.x + s * axis.y
		self.m21 = 0 + temp.z * axis.y - s * axis.x
		self.m22 = c + temp.z * axis.z

	def set_rotation(self, quaternion):
		self.set(quaternion.get_Matrix4())

	def set_scale(self, vector):
		self.m00 = vector.x
		self.m11 = vector.y
		self.m22 = vector.z
		self.m33 = 1.0

	def __mul__(self, m):
		matrix = Matrix4D()
		matrix.set_all(self.m00 * m.m00 + self.m01 * m.m10 + self.m02 * m.m20 + self.m03 * m.m30,
			self.m00 * m.m01 + self.m01 * m.m11 + self.m02 * m.m21 + self.m03 * m.m31,
			self.m00 * m.m02 + self.m01 * m.m12 + self.m02 * m.m22 + self.m03 * m.m32,
			self.m00 * m.m03 + self.m01 * m.m13 + self.m02 * m.m23 + self.m03 * m.m33,
			self.m10 * m.m00 + self.m11 * m.m10 + self.m12 * m.m20 + self.m13 * m.m30, 
			self.m10 * m.m01 + self.m11 * m.m11 + self.m12 * m.m21 + self.m13 * m.m31,
			self.m10 * m.m02 + self.m11 * m.m12 + self.m12 * m.m22 + self.m13 * m.m32,
			self.m10 * m.m03 + self.m11 * m.m13 + self.m12 * m.m23 + self.m13 * m.m33,
			self.m20 * m.m00 + self.m21 * m.m10 + self.m22 * m.m20 + self.m23 * m.m30, 
			self.m20 * m.m01 + self.m21 * m.m11 + self.m22 * m.m21 + self.m23 * m.m31,
			self.m20 * m.m02 + self.m21 * m.m12 + self.m22 * m.m22 + self.m23 * m.m32,
			self.m20 * m.m03 + self.m21 * m.m13 + self.m22 * m.m23 + self.m23 * m.m33,
			self.m30 * m.m00 + self.m31 * m.m10 + self.m32 * m.m20 + self.m33 * m.m30, 
			self.m30 * m.m01 + self.m31 * m.m11 + self.m32 * m.m21 + self.m33 * m.m31,
			self.m30 * m.m02 + self.m31 * m.m12 + self.m32 * m.m22 + self.m33 * m.m32,
			self.m30 * m.m03 + self.m31 * m.m13 + self.m32 * m.m23 + self.m33 * m.m33)

		return matrix


def normalize(vector):
	magnitude = vector.length()

	if(magnitude == 0.0):
		vector.x *= 0
		vector.y *= 0
		vector.z *= 0
		vector.w *= 0
	else:
		vector.x = vector.x / magnitude
		vector.y = vector.y / magnitude
		vector.z = vector.z / magnitude
		vector.w = vector.w / magnitude

	return vector

def mulfVector4D(scalar, v):
	v.x *= scalar
	v.y *= scalar
	v.z *= scalar
	v.w *= scalar

def mulfMatrix4D(scalar, m):
	matrix = Matrix4D()
	matrix.set_all(scalar * m.m00, scalar * m.m01, scalar * m.m02, scalar * m.m03,
				scalar * m.m10, scalar * m.m11, scalar * m.m12, scalar * m.m13,
				scalar * m.m20, scalar * m.m21, scalar * m.m22, scalar * m.m23,
				scalar * m.m30, scalar * m.m31, scalar * m.m32, scalar * m.m33)
	return matrix


def mulfMatrix3D(scalar, m):
	matrix = Matrix3D()
	matrix.set_all(scalar * m.m00, scalar * m.m01, scalar * m.m02,
			   scalar * m.m10, scalar * m.m11, scalar * m.m12,
			   scalar * m.m20, scalar * m.m21, scalar * m.m22)
	return matrix


def mulfMatrix2D(scalar, m):
	return Matrix2D(m.m00 * scalar, m.m01 * scalar, m.m10 * scalar, m.m11 * scalar)


def mulMatrix3DVector3D(m, vec):
	return Vector3D(m.m00 * vec.x + m.m10 * vec.y + m.m20 * vec.z,
					m.m02 * vec.x + m.m11 * vec.y + m.m21 * vec.z,
					m.m02 * vec.x + m.m12 * vec.y + m.m22 * vec.z)

def mulMatrix4DVector3D(m, vec):
	return Vector3D(m.m00 * vec.x + m.m10 * vec.y + m.m20 * vec.z,
					m.m02 * vec.x + m.m11 * vec.y + m.m21 * vec.z,
					m.m02 * vec.x + m.m12 * vec.y + m.m22 * vec.z)


def determinant_matrix2D(m):
	return m.m00 * m.m11 - m.m01 * m.m10


def inverse_matrix2D(m):
	dt = determinant_matrix2D(m)
	if dt == 0:
		print("Determinant is zero")
		sys.exit(1)
	d = 1.0 / dt
	
	return mulfMatrix2D(d, Matrix2D(m.m11, - m.m01, - m.m10, m.m00))
		

def determinant_matrix3D(m):
	return (m.m00 * (m.m11 * m.m22 - m.m12 * m.m21) -
			m.m01 * (m.m10 * m.m22 - m.m12 * m.m20) +
			m.m02 * (m.m10 * m.m21 - m.m11 * m.m20))


def inverse_matrix3D(m):
	dt = determinant_matrix3D(m)
	if dt == 0:
		print("Determinant is zero")
		sys.exit(1)
	d = 1.0 / dt
	
	det0 = determinant_matrix2D(Matrix2D(m.m11, m.m12, m.m21, m.m22))
	det1 = determinant_matrix2D(Matrix2D(m.m10, m.m12, m.m20, m.m22))
	det2 = determinant_matrix2D(Matrix2D(m.m10, m.m11, m.m20, m.m21)) 
	
	det3 = determinant_matrix2D(Matrix2D(m.m01, m.m02, m.m21, m.m22))
	det4 = determinant_matrix2D(Matrix2D(m.m00, m.m02, m.m20, m.m22)) 
	det5 = determinant_matrix2D(Matrix2D(m.m00, m.m01, m.m20, m.m21))
	
	det6 = determinant_matrix2D(Matrix2D(m.m01, m.m02, m.m11, m.m12)) 
	det7 = determinant_matrix2D(Matrix2D(m.m00, m.m02, m.m10, m.m12))
	det8 = determinant_matrix2D(Matrix2D(m.m00, m.m01, m.m10, m.m11))
	
	matrix = Matrix3D()
	matrix.set_all(det0, -det1, det2, -det3, det4, -det5, det6, -det7, det8)
	return mulfMatrix3D(d, matrix)


def determinant_matrix4D(m):
	return (m.m00 * m.m11 * m.m22 * m.m33 + m.m00 * m.m12 * m.m23 * m.m31 +
			m.m00 * m.m13 * m.m21 * m.m32 + m.m01 * m.m10 * m.m23 * m.m32 +
			m.m01 * m.m12 * m.m20 * m.m33 + m.m01 * m.m13 * m.m22 * m.m30 +
			m.m02 * m.m10 * m.m21 * m.m33 + m.m02 * m.m11 * m.m23 * m.m30 +
			m.m02 * m.m13 * m.m20 * m.m31 + m.m03 * m.m10 * m.m22 * m.m31 +
			m.m03 * m.m11 * m.m20 * m.m32 + m.m03 * m.m12 * m.m21 * m.m30 -
			m.m00 * m.m11 * m.m23 * m.m32 - m.m00 * m.m12 * m.m21 * m.m33 -
			m.m00 * m.m13 * m.m22 * m.m31 - m.m01 * m.m10 * m.m22 * m.m33 -
			m.m01 * m.m12 * m.m23 * m.m30 - m.m01 * m.m13 * m.m20 * m.m32 -
			m.m02 * m.m10 * m.m23 * m.m31 - m.m02 * m.m11 * m.m20 * m.m33 -
			m.m02 * m.m13 * m.m21 * m.m30 - m.m03 * m.m10 * m.m21 * m.m32 -
			m.m03 * m.m11 * m.m22 * m.m30 - m.m03 * m.m12 * m.m20 * m.m31)


def inverse_matrix4D(m):
	dt = determinant_matrix4D(m)

	if dt == 0:
		print("Determinant is zero")
		sys.exit(1)
	d = 1 / dt

	det0 = m.m11 * m.m22 * m.m33 + m.m12 * m.m23 * m.m31 + m.m13 * m.m21 * m.m32 - m.m11 * m.m23 * m.m32 - m.m12 * m.m21 * m.m33 - m.m13 * m.m22 * m.m31

	det1 = m.m01 * m.m23 * m.m32 + m.m02 * m.m21 * m.m33 + m.m03 * m.m22 * m.m31 - m.m01 * m.m22 * m.m33 - m.m02 * m.m23 * m.m31 - m.m03 * m.m21 * m.m32

	det2 = m.m01 * m.m12 * m.m33 + m.m02 * m.m13 * m.m31 + m.m03 * m.m11 * m.m32 - m.m01 * m.m13 * m.m32 - m.m02 * m.m11 * m.m33 - m.m03 * m.m12 * m.m31

	det3 = m.m01 * m.m13 * m.m22 + m.m02 * m.m11 * m.m23 + m.m03 * m.m12 * m.m21 - m.m01 * m.m12 * m.m23 - m.m02 * m.m13 * m.m21 - m.m03 * m.m11 * m.m22

	det4 = m.m10 * m.m23 * m.m32 + m.m12 * m.m20 * m.m33 + m.m13 * m.m22 * m.m30 - m.m10 * m.m22 * m.m33 - m.m12 * m.m23 * m.m30 - m.m13 * m.m20 * m.m32

	det5 = m.m00 * m.m22 * m.m33 + m.m02 * m.m23 * m.m30 + m.m03 * m.m20 * m.m32 - m.m00 * m.m23 * m.m32 - m.m02 * m.m20 * m.m33 - m.m03 * m.m22 * m.m30

	det6 = m.m00 * m.m13 * m.m32 + m.m02 * m.m10 * m.m33 + m.m03 * m.m12 * m.m30 - m.m00 * m.m12 * m.m33 - m.m02 * m.m13 * m.m30 - m.m03 * m.m10 * m.m32

	det7 = m.m00 * m.m12 * m.m23 + m.m02 * m.m13 * m.m20 + m.m03 * m.m10 * m.m22 - m.m00 * m.m13 * m.m22 - m.m02 * m.m10 * m.m23 - m.m03 * m.m12 * m.m20

	det8 = m.m10 * m.m21 * m.m33 + m.m11 * m.m23 * m.m30 + m.m13 * m.m20 * m.m31 - m.m10 * m.m23 * m.m31 - m.m11 * m.m20 * m.m33 - m.m13 * m.m21 * m.m30

	det9 = m.m00 * m.m23 * m.m31 + m.m01 * m.m20 * m.m33 + m.m03 * m.m21 * m.m30 - m.m00 * m.m21 * m.m33 - m.m01 * m.m23 * m.m30 - m.m03 * m.m20 * m.m31

	det10 = m.m00 * m.m11 * m.m33 + m.m01 * m.m13 * m.m30 + m.m03 * m.m10 * m.m31 - m.m00 * m.m13 * m.m31 - m.m01 * m.m10 * m.m33 - m.m03 * m.m11 * m.m30

	det11 = m.m00 * m.m13 * m.m21 + m.m01 * m.m10 * m.m23 + m.m03 * m.m11 * m.m20 - m.m00 * m.m11 * m.m23 - m.m01 * m.m13 * m.m20 - m.m03 * m.m10 * m.m21

	det12 = m.m10 * m.m22 * m.m31 + m.m11 * m.m20 * m.m32 + m.m12 * m.m21 * m.m30 - m.m10 * m.m21 * m.m32 - m.m11 * m.m22 * m.m30 - m.m12 * m.m20 * m.m31

	det13 = m.m00 * m.m21 * m.m32 + m.m01 * m.m22 * m.m30 + m.m02 * m.m20 * m.m31 - m.m00 * m.m22 * m.m31 - m.m01 * m.m20 * m.m32 - m.m02 * m.m21 * m.m30

	det14 = m.m00 * m.m12 * m.m31 + m.m01 * m.m10 * m.m32 + m.m02 * m.m11 * m.m30 - m.m00 * m.m11 * m.m32 - m.m01 * m.m12 * m.m30 - m.m02 * m.m10 * m.m31

	det15 = m.m00 * m.m11 * m.m22 + m.m01 * m.m12 * m.m20 + m.m02 * m.m10 * m.m21 - m.m00 * m.m12 * m.m21 - m.m01 * m.m10 * m.m22 - m.m02 * m.m11 * m.m20
	
	matrix = Matrix4D()
	matrix.set_all(det0, det1, det2, det3, det4, det5, det6, det7, det8, det9, det10, det11, det12, det13, det14, det15)
	return mulfMatrix4D(d, matrix)


def saturate(x):
	return math.clamp(x, 0.0, 1.0)
