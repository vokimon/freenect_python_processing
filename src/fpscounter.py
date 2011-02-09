import time
import sys

class FpsCounter :
	def __init__(self, period, printdots=True) :
		self.period = period
		self.periodFrames = self.nFrames = 0
		self.printdots = printdots
		self.first = self.last = time.clock()
		
	def tic(self) :
		self.periodFrames+=1
		if self.printdots :
			sys.stdout.write('.')
			sys.stdout.flush()
		if self.periodFrames != self.period : return
		now = time.clock()
		elapsed = now - self.last
		print
		print "FPS: %.4f" % (float(self.periodFrames)/elapsed)
		print "%.2f milliseconds per frame"%(float(elapsed)*1000/self.periodFrames)
		self.last=now
		self.nFrames += self.periodFrames
		self.periodFrames = 0

	def __del__(self) :
		now = time.clock()
		elapsed = now - self.first
		print
		print "FPS: %.4f" % (float(self.nFrames)/elapsed)
		print "%.2f milliseconds per frame"%(float(elapsed)*1000/self.nFrames)


