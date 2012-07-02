from system.odeWorldManager import *
from direct.interval.IntervalGlobal import *

"""
This is an example of animating a kinematic object to act as a moving platform.
In fact, there's not much to explain here, it's just a kinematic animated with a Sequence.

NOTE, however, that the current implementation of moving platform-ability in kinematic
objects has limits. Most importantly, it doesn't support turning ATM (although I will probably
add it) and it doesn't work that well as an elevator. Using it that way will work for
characters, but the dynamic objects will shake and jump when on a platform moving down.
"""

class movingPlatform(kinematicObject):
	def __init__(self):
		return
		
	def setupGeomAndPhysics(self, map, pos, quat=None):
		kinematicObject.__init__(self, map)
		
		self.surfaceFriction = 1.0
		
		model = loader.loadModel("graphics/models/movingPlatformTest.egg")
		
		self.setNodePath(model, self.map.mapRootNode)
		self.setBoxGeom(Vec3(4.8, 3, 0.4))
		
		self.setPos(pos)
		self.setQuat(quat)
		
		self.map.worldManager.addObject(self)
		
		l1 = LerpPosInterval(self.nodePath, 8.0, pos + Vec3(-6, 0, 0), blendType="easeInOut")
		l2 = LerpPosInterval(self.nodePath, 8.0, pos, blendType="easeInOut")
		moveSeq = Sequence(l1, l2)
		
		Sequence(
			Wait(1.5),
			Func(moveSeq.loop),
		).start()
