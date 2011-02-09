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
#	depth = ft.minimum_filter(depth, size=3)
	depth = depth[::downsampling,::downsampling]
	if showIr :
		ir, timestamp3 = freenect.sync_get_video(format=freenect.VIDEO_IR_8BIT)
		ir = ir[::downsampling,::downsampling]
	else :
		# 12ms
		rgb, timestamp2 = freenect.sync_get_video()
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


