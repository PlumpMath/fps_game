from pandac.PandaModules import Point3, Vec3
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject

from system.odeWorldManager import *
from inventory import pickableObject

import random

"""
A grenade class for testing explosions and thus having lots of fun.
"""
class grenade(pickableObject):
	def __init__(self):
		pickableObject.__init__(self, "grenade", 0.2)
		
		self.icon = "./graphics/pickableIcons/grenade.png"
		
		self.pickableType = "pocket"
		self.modelPath = "./graphics/models/grenade.egg"
		
		"""
		Here we setup the geom size.
		See pickableObject class to find out what that's about.
		"""
		self.geomSize = (0.06, 0.05, 0.10)
	
	"""
	A method that Player controller uses.
	"""
	def useHeld(self):
		self.throw(300.0)
		taskMgr.doMethodLater(4.0, self.explode, "explosion")
		
	def explode(self, arg=None):
		print "grenade exploding!"
		map = self.map
		pos = self.geom.getPosition()
		
		self.map.worldManager.removeObject(self)
		self.destroy()
		
		"""
		Setup an explosion. It will destroy itself automatically.
		"""
		explosion(map, pos, 300.0, 1.)
