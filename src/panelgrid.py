#!/usr/bin/python

import ctypes
import pygame
import numpy as np
import pygame.surfarray
import videosink


class PannelGrid :
	"""
	This class provides abstraction to a pygame window surface
	splitted into many panes of a given size forming a grid.
	"""
	def __init__(self, name, paneSize, colsrows) :
		fullsize = [a*b for a,b in zip(paneSize,colsrows)]
		pygame.init()
		pygame.display.set_caption(name)
		pygame.display.set_mode(fullsize,
#			pygame.DOUBLEBUF|
#			pygame.HWSURFACE|
#			pygame.FULLSCREEN|
#			pygame.OPENGL|
			0)
		self.screen = pygame.display.get_surface()
		self.colsrows = colsrows
		self.screenBuffer = pygame.surfarray.pixels2d(self.screen)
		self.splits = [np.vsplit(v,self.colsrows[0]) for v in np.hsplit(self.screenBuffer,self.colsrows[1])]
		self.videoSink = None

	def pane(self, col, row) :
		"""Returns the numpy matrix for a given pane"""
		return self.splits[col][row]
	def panes(self) :
		"""Returns a matrix of all panes matrix"""
		return self.splits
	def display(self) :
		"""Dumps the panes to the actual window"""
		if self.videoSink : self.videoSink.run(self.screenBuffer)
#		if self.videoSink : self.videoSink.run(self.pane(0,0))
		pygame.display.flip()
	def packed(self, r,g,b) :
		return ctypes.c_uint32(sum(c<<shift for c,shift in zip((r,g,b), self.screen.get_shifts())))
	def toggle_video_capture(self) :
		if self.videoSink :
			self.videoSink.close()
			self.videoSink = None
			return
		self.videoSink = videosink.VideoSink(self.screenBuffer.shape, "output",rate=5)

def main() :
	import time
	import sys

	size = 640,480
	grid = 2,2

	pygame.init()
	panel = PannelGrid("PannelGrid demo", size, grid)
	
	x=0
	firstTic=time.clock()
	tic = time.clock()
	nFrames=0
	stop=False
	while not stop :
		for event in pygame.event.get() :
			if event.type == pygame.QUIT : 
				stop = True
			if event.type == pygame.KEYDOWN  :
				if event.key == pygame.K_ESCAPE :
					stop = True
				if( event.key == pygame.K_f ):
				   pygame.display.toggle_fullscreen()
				if( event.key == pygame.K_v ):
				   panel.toggle_video_capture()
		panel.pane(0,0)[:,:] = panel.packed(0xff-x,0x00+x,0x00+x)
		panel.pane(1,0)[:,:] = panel.packed(0x00+x,0xff-x,0x00+x)
		panel.pane(1,1)[:,:] = panel.packed(0x00+x,0x00+x,0xff-x)
		panel.pane(0,1)[:,:] = panel.packed(x,x,x)
		panel.display()
		sys.stdout.write(".")
		sys.stdout.flush()
		x+=1
		x&=0xff
		nFrames+=1
		if nFrames%16 == 0 :
			toc = time.clock()
			wallClock = toc - tic
			tic = toc
			print
			print "FPS: %.4f" % (float(nFrames)/wallClock)
			print "%.2f milliseconds per frame"%(float(wallClock)*1000/nFrames)
			nFrames=0

if __name__ == "__main__" :
	main()




