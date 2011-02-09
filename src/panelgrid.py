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
	Axis and sizes are ordered x,y or cols,rows which, is more 
	natural to resolutions, but strides are smaller on x, so 
	loops will do better caching for each row then for each col.
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
		self.screenBuffer = pygame.surfarray.pixels2d(self.screen).swapaxes(0,1)
		self.splits = [np.hsplit(v,self.colsrows[0]) for v in np.vsplit(self.screenBuffer,self.colsrows[1])]
		self.videoSink = None
		self.letterR = np.array([[c!=" " for c in row] for row in [
			"******* ",
			"********",
			"**    **",
			"**   ***",
			"******* ",
			"******  ",
			"**  *** ",
			"**   ***",
			"**    **",
			"**    **",
		]], dtype=bool)
		self.blink = 0

	def pane(self, row, col) :
		"""Returns the numpy matrix for a given pane"""
		return self.splits[row][col]
	def panes(self) :
		"""Returns a matrix of all panes matrix"""
		return self.splits
	def display(self) :
		"""Dumps the panes to the actual window"""
		if self.videoSink :
			self.videoSink.run(self.screenBuffer)
			if not self.blink & 0x08 :
				self.screenBuffer[5:21,-19:-5] = 0x00000000
				self.screenBuffer[6:20,-18:-6] = 0x00ef0000
				self.screenBuffer[8:18,-16:-8][self.letterR] = 0x00000000
			self.blink+=1
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
	import fpscounter

	size = 640,480
	grid = 2,2

	pygame.init()
	panel = PannelGrid("PannelGrid demo", size, grid)
	
	x=0
	stop=False
	singleAcces=False
	fps = fpscounter.FpsCounter(period=16)
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
				if( event.key == pygame.K_s ):
					singleAcces = not singleAcces
					print "Switching to", "indexed mode" if singleAcces else "multipane mode"
		if singleAcces : 
			panel.pane(0,0)[:,:] = panel.packed(0xff-x,0x00+x,0x00+x)
			panel.pane(1,0)[:,:] = panel.packed(0x00+x,0xff-x,0x00+x)
			panel.pane(1,1)[:,:] = panel.packed(0x00+x,0x00+x,0xff-x)
			panel.pane(0,1)[:,:] = panel.packed(x,x,x)
			panel.pane(0,1)[:10,:] = panel.packed(0x00,0x00,0xaf)
			panel.pane(0,1)[:,:10] = panel.packed(0x00,0xaf,0x00)
		else :
			(
			(NW,NE),
			(SW,SE),
			) = panel.panes()
			NW[:,:] = panel.packed(0xff-x,0x00+x,0x00+x)
			SW[:,:] = panel.packed(0x00+x,0xff-x,0x00+x)
			SE[:,:] = panel.packed(0x00+x,0x00+x,0xff-x)
			NE[:,:] = panel.packed(x,x,x)
			NE[:10,:] = panel.packed(0x00,0x00,0xaf)
			NE[:,:10] = panel.packed(0x00,0xaf,0x00)
		panel.display()
		x+=1
		x&=0xff

		fps.tic()

if __name__ == "__main__" :
	main()




