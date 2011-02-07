import time
import sys

class FpsCounter :
	def __init__(self, period, printdots=True) :
		self.period = period
		self.nFrames = 0
		self.printdots = printdots
		self.last = time.clock()

	def tic(self) :
		self.nFrames+=1
		if self.printdots :
			sys.stdout.write('.')
			sys.stdout.flush()
		if self.nFrames != self.period : return
		now = time.clock()
		elapsed = now - self.last
		print
		print "FPS: %.4f" % (float(self.nFrames)/elapsed)
		print "%.2f milliseconds per frame"%(float(elapsed)*1000/self.nFrames)
		self.last=now
		self.nFrames = 0



