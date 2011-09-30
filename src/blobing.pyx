import numpy as np
cimport numpy as np

cdef void floodFill_processPoint(
	np.ndarray[np.uint16_t, ndim=2] inputImage,
	np.ndarray[np.uint8_t, ndim=2] output, 
	Py_ssize_t x, Py_ssize_t y, level=0) :
	if level > 40000 : return
	cdef int threshold = 6
	cdef Py_ssize_t W,H
	H,W = inputImage.shape[0], inputImage.shape[1]
	if x<0 : return
	if y<0 : return
	if x>=W-10 : return
	if y>=H-10 : return
	if output[y,x] != 0 : return
	if inputImage[y,x]>threshold : return
	output[y,x] = 1
	# first the ones close in cache
	floodFill_processPoint(inputImage, output, x-1,y+0, level+1)
	floodFill_processPoint(inputImage, output, x+1,y+0, level+1)
	floodFill_processPoint(inputImage, output, x+0,y-1, level+1)
	floodFill_processPoint(inputImage, output, x+0,y+1, level+1)

cpdef floodFill(inputImage, output, initialX, initialY) :
	""" fills the containing the initial point using a flood fill
	algorithm with 4 neighbours.
	"""
	output[...] = 0
	cdef Py_ssize_t x = initialX
	cdef Py_ssize_t y = initialY
	while x<inputImage.shape[1] and inputImage[y,x] == 255 : x+=1
	if x==inputImage.shape[1] : return
	floodFill_processPoint(inputImage, output, x,y) 


# http://en.wikipedia.org/wiki/Blob_extraction

class _BlobClassDatabase(object) :
	def __init__(self) :
		self._blobs2={}
		self._last=0
		self._recycled=[]
	def new(self,x,y) :
		if self._recycled :
			key = self._recycled.pop()
			self._blobs2[key] = (1,(x,y),(x,y),(x,y))
			return key
		self._last+=1
		self._blobs2[self._last] = (1,(x,y),(x,y),(x,y))
		return self._last
	def join(self, one, other) :
		""" Joins 'other' class into 'one', updates the first ocurrence of one,
		and returns the first occurence of the removed 'other' class"""
		n1, first1, (minX1,minY1), (maxX1,maxY1) = self._blobs2[one]
		n2, first2, (minX2,minY2), (maxX2,maxY2) = self._blobs2[other]
		self._blobs2[one] = (
			n1+n2, 
			min(first1[::-1], first2[::-1])[::-1],
			(min(minX1,minX2), min(minY1,minY2)),
			(max(maxX1,maxX2), max(maxY1,maxY2)),
			)
		del self._blobs2[other]
		self._recycled.append(other)
		return first2
	def expand(self, one, x, y) :
		n, first, (minX,minY), (maxX,maxY) = self._blobs2[one]
		self._blobs2[one] = n+1, first, (min(minX,x), minY), (max(maxX,x), y)
		return one

cpdef blobDetect(
	np.ndarray[np.uint16_t, ndim=2] depth, 
	np.ndarray[np.uint16_t, ndim=2] gradientx, 
	np.ndarray[np.uint16_t, ndim=2] gradienty, 
	np.ndarray[np.uint16_t, ndim=2] output
	) :
	
	cdef Py_ssize_t H = depth.shape[0]
	cdef Py_ssize_t W = depth.shape[1]
	threshold = 3
	output.fill(0)
	blobs = _BlobClassDatabase()
	depthClass = 0
	infiniteDepth = 255
	cdef Py_ssize_t x, y
	for y in xrange(1,H) :
		for x in xrange(W) :
			if gradienty[y,x] == infiniteDepth :
				output[y,x] = depthClass
				continue
			northClass = output[y-1,x] if y else depthClass
			westClass = output[y,x-1] if x else depthClass
			northConnected = northClass != depthClass and gradienty[y,x] < threshold
			westConnected = westClass != depthClass and gradientx[y,x] < threshold
			if northConnected and westConnected and northClass != westClass :
				firstX, firstY = blobs.join(northClass, westClass)
				output[firstY:y,:][output[firstY:y,:]==westClass] = northClass
				output[y,:x][output[y,:x]==westClass] = northClass
			if northConnected :
				output[y,x] = blobs.expand(northClass,x,y)
			elif westConnected :
				output[y,x] = blobs.expand(westClass,x,y)
			else :
				output[y,x] = blobs.new(x,y)
	return blobs._blobs2


cpdef distanceTransform(
	np.ndarray[np.uint16_t, ndim=2] profile,
	np.ndarray[np.uint16_t, ndim=2] output,
	) :

	"""http://www.citr.auckland.ac.nz/~rklette/Books/MK2004/pdf-LectureNotes/08slides.pdf"""
	
	cdef Py_ssize_t H = profile.shape[0]
	cdef Py_ssize_t W = profile.shape[1]
	cdef Py_ssize_t i, j
	for j in xrange(1,H) :
		for i in xrange(W) :
			if profile[j,i] > 4 :
				output[j,i] = 0
				continue
			output[j,i] = 1+min(
				output[j-1,i],
				output[j,i-1],
				)
	for j in xrange(H-2,0,-1) :
		for i in xrange(W-2,0,-1) :
			output[j,i] = min(
				output[j,i],
				output[j+1,i]+1,
				output[j,i+1]+1,
				)

cpdef findRidge(
	np.ndarray[np.uint16_t, ndim=2] borderDistance,
	np.ndarray[np.uint16_t, ndim=2] output,
	) :

	height, width = borderDistance.shape[0], borderDistance.shape[1]
	output[:]=0
	cdef int N,S,E,W,C
	cdef Py_ssize_t i, j
	for j in xrange(1,height-1) :
		for i in xrange(1,width-1) :
			C = borderDistance[j,i]
			if C == 0 :
				output[j,i] = 0
				continue
			W = borderDistance[j,i-1]
			E = borderDistance[j,i+1]
			N = borderDistance[j-1,i]
			S = borderDistance[j+1,i]
			if abs(W-E) == 2 : continue
			if abs(N-S) == 2 : continue
			output[j,i] = 4







