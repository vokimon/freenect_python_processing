#!/usr/bin/python

# enables runtime compilation of pyx modules
import pyximport; pyximport.install()
import colormap

import fpscounter
import pygame
import panelgrid
import freenect
import numpy as np

downsampling = 2
kinnectSize = 640,480
size = [x//downsampling for x in kinnectSize]
maxRealDepth=1080
infiniteDepth=2047


def pack(r,g,b) :
	"""Packs red, green and blue components into a XRGB 32bit number. (X is panning)"""
	return sum(c<<shift for c,shift in zip((r,g,b),(16,8,0)))
	return sum((int(c)&0xff)<<shift for c,shift in zip((r,g,b),(16,8,0))) # safer


# RGB palettes

# To see sign changes (requires reinterpreting int8 as uint8)
signPalette = [
		x*0x010000+0x700000 for x in xrange(0x80)
	] + [
		0x00ff00-x*0x000100 for x in xrange(0x80)
	]
signPalette[0]=0x0

# requires infiniteDepth to be maped to 0
# first segment is for too close depth, they may appear 
# but do not use dynamic range for them just a different scale.
depthColorPalete = [
		0
	] + [
		pack(0,x,0xff-x)
		for x in xrange(1,256)
	]+[
		pack(0xff-abs(int(x)-0x7f)*2, 0xff-int(x), int(x))
		for x in np.linspace(0,255,maxRealDepth-256)
	]

greyScale = [pack(x,x,x) for x in xrange(256)]

def mapToColor(input, output, palette, infiniteColor=None, drawScale=True) :
	"""Builds a 32 bits XRGB packed color image by applying a palette to an index image"""
	np.take(palette, input, axis=0, out=output, mode='wrap')
	if infiniteColor is not None :
		output[input==infiniteDepth] = infiniteColor
	if drawScale :
		for y in xrange(input.shape[1]) :
			output[-10:-1,y] = palette[y*len(palette)/input.shape[1]]

def packArray(unpacked, packed) :
	"""Builds a 32 bits XRGB packed color image from a R,G,B 3D
	uint8 X,Y,3 matrix."""
	packed[:,:]  = unpacked[:,:,0]
	packed[:,:] <<= 8
	packed[:,:] += unpacked[:,:,1]
	packed[:,:] <<= 8
	packed[:,:] += unpacked[:,:,2]


pygame.init()
panel = panelgrid.PannelGrid("kinect view", size, (2,1))
(
(output_L, output_R),
) = panel.panes()

import scipy.ndimage.filters as ft

rgb_packed  = np.zeros(size, np.uint32)

print "Action!"
finnish = False
showIr = False
fps = fpscounter.FpsCounter(period=16)

while not finnish :
	# 8ms
	depth, timestamp = freenect.sync_get_depth()
	depth = depth.swapaxes(0,1)
#	depth = ft.minimum_filter(depth, size=3)
	depth = depth[::downsampling,::downsampling]
	if showIr :
		ir, timestamp3 = freenect.sync_get_video(format=freenect.VIDEO_IR_8BIT)
		ir = ir.swapaxes(0,1)
		ir = ir[::downsampling,::downsampling]
	else :
		# 12ms
		rgb, timestamp2 = freenect.sync_get_video()
		rgb = rgb.swapaxes(0,1)
		rgb = rgb[::downsampling,::downsampling,:]

	# 12 ms, 18ms
	colormap.mapToColor(depth, output_R, colormap.depthColorPalete, 0x000000)
	if showIr :
		colormap.mapToColor(ir, output_L, colormap.greyScale)
	else:
		colormap.packArray(rgb, output_L) # 5ms, 7ms

	panel.display()

	for event in pygame.event.get() :
		if event.type == pygame.QUIT :
			finish = True
		if event.type == pygame.KEYDOWN  :
			if event.key == pygame.K_ESCAPE :
				finnish = True
			if event.key == pygame.K_q :
				finnish = True
			if event.key == pygame.K_i :
				showIr = not showIr
			if event.key == pygame.K_f :
				pygame.display.toggle_fullscreen()
			if event.key == pygame.K_v :
				panel.toggle_video_capture()
	fps.tic()

print "Stopping kinect"
freenect.sync_stop()
print "Stopping pygame"


