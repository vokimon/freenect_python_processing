#!/usr/bin/python


import pygame
from pygame.locals import QUIT, KEYDOWN
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
		pygame.display.set_caption(name)
		pygame.display.set_mode(fullsize,0)
		screen = pygame.display.get_surface()
		screenBuffer = pygame.surfarray.pixels3d(screen)
		self.splits = [np.hsplit(v,colsrows[1]) for v in np.vsplit(screenBuffer,colsrows[0])]
	def pane(self, col, row) :
		"""Returns the numpy matrix for a given pane"""
		return self.splits[col][row]
	def panes(self) :
		"""Returns a matrix of all panes matrix"""
		return self.splits
	def display(self) :
		"""Dumps the panes to the actual window"""
		pygame.display.flip()


def main() :
	import time

	size = 640,480
	grid = 2,2

	pygame.init()
	panel = PannelGrid("PannelGrid demo", size, grid)
	nFrames = 0
	x=0
	tic = time.clock()
	stop = False
	while not stop :
		for event in pygame.event.get() :
			if event.type == QUIT : sys.exit(0)
			if event.type == KEYDOWN  :
				if event.key == pygame.K_ESCAPE :
					stop = True
		
		panel.pane(0,0)[:,:] = 0x0ff,0,x
		panel.pane(1,0)[:,:] = x,0x0ff-x,0
		panel.pane(1,1)[:,:] = 0,0,0x0ff
		panel.pane(0,1)[:,:] = x,0,0x0ff-x
		panel.display()
		sys.stdout.write(".")
		sys.stdout.flush()
		x+=1
		nFrames+=1
	elapsed = time.clock() - tic
	print
	print "%.2f FPS, %.6f ms per frame"%(float(nFrames)/elapsed, float(elapsed)*1000/nFrames)

if __name__ == "__main__" :
	main()




