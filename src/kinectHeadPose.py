#!/usr/bin/python


# enables runtime compilation of pyx modules
import pyximport; pyximport.install()
import blobing
import colormap
import time


import fpscounter
import pygame
import sys
import panelgrid

import freenect
import numpy as np

downsampling = 2
kinnectSize = 640,480
width,height = size = [x//downsampling for x in kinnectSize]
coarseGrain = 16
coarseSize = [x/coarseGrain for x in size ]
maxRealDepth=1080
infiniteDepth=2047

def image2D(size, dtype) :
	return np.zeros(size[::-1], dtype=dtype)

def drawPoint(image, point, r, color) :
	x,y = point
	image[y-r:y+r,x-r:x+r]+=color

def drawBox(image, topLeft, bottomRight, color) :
	x1,y1 = topLeft
	x2,y2 = bottomRight
	image[y1:y2,x1]=color
	image[y1:y2,x2]=color
	image[y1,x1:x2]=color
	image[y2,x1:x2]=color

def drawFullBox(image, topLeft, bottomRight, color) :
	x1,y1 = topLeft
	x2,y2 = bottomRight
	image[y1:y2,x1:x2]=color

def pack(r,g,b) :
	"""Packs red, green and blue components into a XRGB 32bit number. (X is panning)"""
	return sum(c<<shift for c,shift in zip((r,g,b),(16,8,0)))
	return sum((int(c)&0xff)<<shift for c,shift in zip((r,g,b),(16,8,0))) # safer


downgradedDepth = image2D(size, np.uint8)
def visualizeDepthInGrey(depth, outputRgb, infiniteColor = None) :
#	downgradedDepth[:] = depth>>3
	downgradedDepth = depth
	colormap.mapToColor(downgradedDepth, outputRgb, colormap.greyScale, infiniteColor)

import math
# http://nicolas.burrus.name/index.php/Research/KinectCalibration
depthMap1 = [ 0.1236 * math.tan(i/2842.5 + 1.1863) for i in xrange(1080) ]
# http://groups.google.com/group/openkinect/browse_thread/thread/31351846fd33c78/e98a94ac605b9f21
depthMap2 = [ 1./(-i*0.0030711016 + 3.3309495161) for i in xrange(1080) ]
# my simplification of depthMap2
depthMap3 = [ 325.62/(1084-i) for i in xrange(1080) ]
depthMap = depthMap2

def depthKinnectToMeters(intDepth, floatDepth) :
	""" Converts the depth value provided by Kinnect 
	to a distance in metters from the focus """
	np.take(depthMap, intDepth, axis=0, out=floatDepth, mode='clip')

def quantize(floatArray, intArray, minimum, maximum) :
	floatArray -=minimum
	floatArray[floatArray<0] = 0
	floatArray /=(maximum-minimum)
	floatArray *= 1<<(intArray.itemsize*8)
	intArray[:] = floatArray


def computeGradients(input, outputX, outputY) :
	outputY[1,:] = 0xff
	outputY[1:,:] = input[1:,:]
	outputY[1:,:]-= input[:-1,:]
	outputY[outputX>0xA000] *= -1
	outputY[input==infiniteDepth]=0xffff

	outputX[:,1] = 0xff
	outputX[:,1:] = input[:,1:]
	outputX[:,1:]-= input[:,:-1]
	outputX[outputY>0xA000] *= -1
	outputX[input==infiniteDepth]=255

def computeMinMax(depth, minimum, maximum, minmax) :
	ft.maximum_filter(depth, size=3, output=maximum)
	ft.minimum_filter(depth, size=3, output=minimum)
#	assert not (maximum<minimum).any()
	minimum[maximum==infiniteDepth]=0
	minmax[:] = 0
	minmax[maximum>minimum+10] = 255

def newBackroundPoints(depth, backgroundDepth) :
	result = depth>=backgroundDepth
	result &= depth!=infiniteDepth
	return result

def blobPixels(blob, depth, labeling) :
	y1,x1 = blob[3]
	y2,x2 = blob[4]
	blobDepth = depth[y1:y2,x1:x2]
	blobLabeling = labeling[y1:y2,x1:x2]
	result = blobDepth[blobLabeling==blob[0]]
	return result[result<infiniteDepth]

pygame.init()
panel = panelgrid.PannelGrid("Kinect Process", size, (3,3))
(
(output_NW, output_NN, output_NE),
(output_WW, output_CC, output_EE),
(output_SW, output_SS, output_SE),
) = panel.panes()

floatDepth = image2D(size, np.float)
quantizedDepth = image2D(size, np.uint16)

flood = image2D(size, np.uint8)
blobImage = image2D(size, np.uint16)

import scipy.ndimage.filters as ft
import scipy.ndimage.morphology as mf

gradientx = image2D(size, np.uint16)
gradienty = image2D(size, np.uint16)
maximum = image2D(size, np.uint16)
minimum = image2D(size, np.uint16)
minmax  = image2D(size, np.uint16)
backgroundDepth  = image2D(size, np.uint16)
rgb_back  = image2D(size, np.int32)
rgb_packed  = image2D(size, np.int32)
laplace  = image2D(size, np.int16)

distanceTransform = image2D(size, np.uint16)
ridge = image2D(size, np.uint16)

flooding = False
gradientBlob = False

print "Action!"
oldDepth=None
finnish = False
fps = fpscounter.FpsCounter(period=16)

while not finnish :
	depth, timestamp = freenect.sync_get_depth()
	depth = depth[::downsampling,::downsampling]
	ft.minimum_filter(depth, size=downsampling, output=depth)
	rgb, timestamp2 = freenect.sync_get_video()
	rgb = rgb[::downsampling,::downsampling,:]
	
	colormap.packArray(rgb, rgb_packed)
	if oldDepth is None : oldDepth = depth

	# consider infinite those depths close to background
	newBackground = newBackroundPoints(depth, backgroundDepth)
	backgroundDepth[newBackground] = depth[newBackground]

	depthKinnectToMeters(depth, floatDepth)
	quantize(floatDepth, quantizedDepth,depthMap[255],depthMap[-1])
	quantizedDepth >>=4

	depth[depth>=backgroundDepth-10]=infiniteDepth

	computeMinMax(depth, maximum, minimum, minmax)

	rgb_back.fill(0x000000)
	rgb_back[minmax==0] = rgb_packed[minmax==0]

	if flooding :
		blobing.floodFill(minmax, flood, width/2, height/2)

	if gradientBlob :
		computeGradients(depth, gradientx, gradienty)
		blobLabels = blobing.blobDetect(depth, gradientx, gradienty, blobImage)
	else :
		blobLabels = blobing.blobDetect(depth, minmax, minmax, blobImage)

	blobs = [
		(key, n, first, topLeft, bottomRight)
		for key, (n, first, topLeft, bottomRight) in blobLabels.items()
		if bottomRight[0]-topLeft[0] > 4 and bottomRight[1]-topLeft[1] > 4
		]

	for key, n, first, topLeft, bottomRight in blobs :
		drawBox(blobImage, topLeft, bottomRight, key)

	blobs.sort(key=lambda a:a[1])

#	mf.distance_transform_cdt(minmax==0, distances=distanceTransform, metric='taxicab')
	blobing.distanceTransform(minmax, distanceTransform)
	blobing.findRidge(distanceTransform, ridge)
	colormap.mapToColor(
		quantizedDepth, output_NN, 
		palette=colormap.depthColorPalete,
		infiniteColor=0xff0000)
	# NE: minmax borders
	output_NE[:,:] = minmax
	output_NE <<=16
	if flooding :
		# Flooding algorithm
		output_SS[...] = 0
		output_SS[flood>0] = 0xff0000
		drawPoint(output_SS, (width/2, height/2), 2, 0xff7f00)
	else :
		colormap.mapToColor(ridge, output_SS, np.array([0x0, 0xff0000, 0x00ff00, 0xffff00, 0x00ffff], dtype=np.int32))

	colormap.mapToColor(backgroundDepth, output_CC, colormap.greyScale, 0x000000)
	colormap.mapToColor(blobImage, output_EE, colormap.blobPalette)
	if blobs :
		drawBox(output_EE, blobs[-1][3], blobs[-1][4], 0xffff00)

		blobDepths = blobPixels(blobs[-1], depth, blobImage)
#		blobMin, blobMean, blobMax = blobDepths.min(), blobDepths.mean(), blobDepths.max()
#		print blobMin, blobMean, blobMax
#		output_EE[ abs(depth-blobMean)<3 ] = 0xff00ff
#		output_EE[ abs(depth-blobMax)<3 ]  = 0xffff00
#		output_EE[ abs(depth-blobMin)<3 ]  = 0x00ff00
	else : print "no blobs"

	output_NW[...] = rgb_packed
	output_WW[...] = rgb_back
	colormap.mapToColor(distanceTransform, output_SE, colormap.depthColorPalete[::16])

	panel.display()

	oldDepth = depth
	for event in pygame.event.get() :
		if event.type == pygame.QUIT :
			finish = True
		if event.type == pygame.KEYDOWN  :
			if event.key == pygame.K_ESCAPE :
				finnish = True
			if event.key == pygame.K_q :
				finnish = True
			if event.key == pygame.K_r :
				backgroundDepth[:] = 0
			if event.key == pygame.K_l :
				flooding = not flooding
			if event.key == pygame.K_f :
				pygame.display.toggle_fullscreen()
			if event.key == pygame.K_v :
				panel.toggle_video_capture()
	fps.tic()
del fps

print "Stopping kinect"
freenect.sync_stop()
print "Stopping pygame"




