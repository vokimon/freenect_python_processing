#!/usr/bin/python

import subprocess
import numpy as np

class VideoSink(object) :
	def __init__( self, size, filename="output", rate=1, byteorder="bgra" ) :
		self.size = size
		cmdstring  = ('mencoder',
			'/dev/stdin',
			'-demuxer', 'rawvideo',
			'-rawvideo', 'w=%i:h=%i'%size+":fps=%i:format=%s"%(rate,byteorder),
			'-o', filename+'.avi',
			'-ovc', 'lavc',
			)
		self.p = subprocess.Popen(cmdstring, stdin=subprocess.PIPE, shell=False)

	def run(self, image) :
		assert image.shape == self.size[::-1]
#		image.swapaxes(0,1).tofile(self.p.stdin) # should be faster but it is indeed slower
		self.p.stdin.write(image.tostring())
	def close(self) :
		self.p.stdin.close()

	
if __name__ == "__main__" :
	import sys
	W,H = 480,360
	rate = 40
	video = VideoSink((W,H), "test", rate=rate, byteorder="bgra")
	image = np.ones((H,W), np.uint32)
	for color in (
		0x00ff0000, # red
		0x0000ff00, # green
		0x000000ff, # blue
		0xffff0000, # red with alpha (should be ignored)
		) :
		image[:] = color
		for i in xrange(rate) : video.run(image)
	# Turn green from left to right
	for col in xrange(0,W,2) :
		image[:,col] = 0x0000ff00
		video.run(image)
	# Turn blue from up to down
	for row in xrange(0,H,2) :
		image[row,:] = 0x000000ff
		video.run(image)
	for r in xrange(400) :
		video.run(np.fromfunction(lambda g,b : np.uint32(b)+0x100*g+0x10000*r,  shape=(H,W), dtype=np.uint32))
		print ".",
		sys.stdin.flush()
	video.close()



