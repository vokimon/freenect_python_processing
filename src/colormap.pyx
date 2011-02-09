
# this module contains routines to convert among image formats
# using index to color maps, or packing colors together

import numpy as np
cimport numpy as np

cdef np.uint16_t maxRealDepth=1080
cdef np.uint16_t infiniteDepth=2047


def pack(r,g,b) :
	"""Packs red, green and blue components into a XRGB 32bit number. (X is panning)"""
	return sum(c<<shift for c,shift in zip((r,g,b),(16,8,0)))
	return sum((int(c)&0xff)<<shift for c,shift in zip((r,g,b),(16,8,0))) # safer


# RGB palettes

# To see sign changes (requires reinterpreting int8 as uint8)
signPalette = np.array([
		x*0x010000+0x700000 for x in xrange(0x80)
	] + [
		0x00ff00-x*0x000100 for x in xrange(0x80)
	], dtype=np.int32)
signPalette[0]=0x0

# requires infiniteDepth to be maped to 0
# first segment is for too close depth, they may appear 
# but do not use dynamic range for them just a different scale.
depthColorPalete = np.array([
		0
	] + [
		pack(0,x,0xff-x)
		for x in xrange(1,256)
	]+[
		pack(0xff-abs(int(x)-0x7f)*2, 0xff-int(x), int(x))
		for x in np.linspace(0,255,maxRealDepth-256)
	], np.int32)

greyScale = np.array([pack(x,x,x) for x in xrange(256)], np.int32)


cdef map8ToColor(
		np.ndarray[np.uint8_t, ndim=2] input,
		np.ndarray[np.int32_t, ndim=2] output,
		np.ndarray[np.int32_t, ndim=1] palette, 
		infiniteColor=None, 
		drawScale=True,
	):
	"""8 bit implementation of mapToColor"""
	cdef Py_ssize_t x,y
	cdef np.uint16_t paletteLength = len(palette)
	cdef np.int32_t infiniteColorValue
	if infiniteColor is  None :
		for y in xrange(input.shape[1]) :
			for x in xrange(input.shape[0]) :
				output[x,y] = palette[input[x,y]%paletteLength]
	else :
		infiniteColorValue = infiniteColor
		for y in xrange(input.shape[1]) :
			for x in xrange(input.shape[0]) :
				output[x,y] = (
					infiniteColorValue
					if input[x,y] == infiniteDepth
					else palette[input[x,y]%paletteLength]
					)
	if drawScale :
		for y in xrange(input.shape[1]) :
			output[-10:-1,y] = palette[y*len(palette)/input.shape[1]]

cdef map16ToColor(
		np.ndarray[np.uint16_t, ndim=2] input,
		np.ndarray[np.int32_t, ndim=2] output,
		np.ndarray[np.int32_t, ndim=1] palette, 
		infiniteColor=None, 
		drawScale=True,
	):
	"""16 bit implementation of mapToColor"""
	cdef Py_ssize_t x,y
	cdef np.uint16_t paletteLength = len(palette)
	cdef np.int32_t infiniteColorValue
	if infiniteColor is None :
		for y in xrange(input.shape[1]) :
			for x in xrange(input.shape[0]) :
				output[x,y] = palette[input[x,y]%paletteLength]
	else:
		infiniteColorValue = infiniteColor
		for y in xrange(input.shape[1]) :
			for x in xrange(input.shape[0]) :
				output[x,y] = (
					infiniteColorValue
					if input[x,y] == infiniteDepth
					else palette[input[x,y]%paletteLength]
					)
	if drawScale :
		for y in xrange(input.shape[1]) :
			output[-10:-1,-1-y] = palette[y*len(palette)/input.shape[1]]

def mapToColor(
		input,
		output,
		palette, 
		infiniteColor=None, 
		drawScale=True,
	):
	"""Builds a 32 bits XRGB packed color image by applying a palette to an index image"""
#	np.take(palette, input, axis=0, out=output, mode='wrap')
	if input.dtype == np.uint16 :
		map16ToColor(input, output, palette, infiniteColor, drawScale)
	elif input.dtype == np.uint8 :
		map8ToColor(input, output, palette, infiniteColor, drawScale)


cpdef packArray(
		np.ndarray[np.uint8_t, ndim=3] unpacked,
		np.ndarray[np.int32_t, ndim=2] packed,
	) :
	"""Builds a 32 bits XRGB packed color image from a R,G,B 3D
	uint8 X,Y,3 matrix."""
	cdef Py_ssize_t i,j
	cdef np.uint8_t r,g,b
	cdef np.uint32_t color
	for j in xrange(unpacked.shape[1]) :
		for i in xrange(unpacked.shape[0]) :
			color = unpacked[i,j,0] # r
			color = color << 8
			color += unpacked[i,j,1] # g
			color = color << 8
			color += unpacked[i,j,2] # b
			packed[i,j] = color




