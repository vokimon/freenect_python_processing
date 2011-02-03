#!/usr/bin/python

import ctypes
import pygame
from pygame import QUIT, KEYDOWN, K_ESCAPE, K_f
import numpy as np
import sys
import pygame.surfarray


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
		screenBuffer = pygame.surfarray.pixels2d(self.screen)
		self.splits = [np.vsplit(v,self.colsrows[0]) for v in np.hsplit(screenBuffer,self.colsrows[1])]

	def pane(self, col, row) :
		"""Returns the numpy matrix for a given pane"""
		return self.splits[col][row]
	def panes(self) :
		"""Returns a matrix of all panes matrix"""
		return self.splits
	def display(self) :
		"""Dumps the panes to the actual window"""
		pygame.display.flip()
	def packed(self, r,g,b) :
		return ctypes.c_uint32(sum(c<<shift for c,shift in zip((r,g,b), self.screen.get_shifts())))

def main() :
	import time

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
			if event.type == QUIT : 
				stop = True
			if event.type == KEYDOWN  :
				if event.key == K_ESCAPE :
					stop = True
				if( event.key == K_f ):
				   pygame.display.toggle_fullscreen()
		panel.pane(0,0)[:,:] = panel.packed(0xff-x,0x00+x,0x00+x)
		panel.pane(1,0)[:,:] = panel.packed(0x00+x,0xff-x,0x00+x)
		panel.pane(1,1)[:,:] = panel.packed(0x00+x,0x00+x,0xff-x)
		panel.pane(0,1)[:,:] = panel.packed(x,x,x)
		panel.display()
		sys.stdout.write(".")
		sys.stdout.flush()
		x+=1
		x&=0xff
		toc = time.clock()
#		print "%2.5f"%(toc-tic)
		tic = toc
		nFrames+=1
	wallClock = time.clock()-firstTic
	print
	print "FPS: %.4f" % (float(nFrames)/wallClock)
	print "%.2f milliseconds per frame"%(float(wallClock)*1000/nFrames)

if __name__ == "__main__" :
	main()




