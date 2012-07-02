from system.odeWorldManager import *
from direct.interval.IntervalGlobal import *

class chair(staticObject):
	def __init__(self, map, model):
		staticObject.__init__(self, map)
		
		self.setNodePath(model)
		self.setBoxGeom(Vec3(.5, .5, 1.2))
		
		self.state = "vacant"
		
		self.map.worldManager.addObject(self)
		
	def selectionCallback(self, character, direction):
		if self.state != "vacant":
			return
		self.state = "taken"
		character.sitOnChair(self)
		
	def setState(self, state):
		self.state = state
