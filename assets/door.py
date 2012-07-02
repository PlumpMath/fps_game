from system.odeWorldManager import *
from direct.interval.IntervalGlobal import *

class doorKey(object):
	def __init__(self, map, keyCodes):
		self.map = map
		self.keyCodes = keyCodes
		
	def pickUp(self, character, dir):
		for key in self.keyCodes:
			character.doorKeysSet.add(key)
		self.destroy()
		
	def update(self, timeStep):
		pass
		
	def destroy(self):
		self.nodePath.remove()
		self.map.removeObject(self.geom)
		self.geom.destroy()

class door(kinematicObject):
	def __init__(self):
		self.keyCode = "general"
		
		self.state = "locked"
		self.speed = 0.5
		self.newH = 0.0
		
	def setupGeomAndPhysics(self, map, pos, quat=None):
		kinematicObject.__init__(self, map)
		
		parentModel = loader.loadModel("graphics/models/door.egg")
		
		for child in parentModel.getChild(0).getChildren():
			if child.getTag("type") == "doorCollider":
				geomSource = child
			elif child.getTag("type") == "door":
				model = child
		
		self.setNodePath(model, self.map.mapRootNode)
		self.setBoxGeomFromNodePath(geomSource)
		
		self.map.worldManager.addObject(self)
		
		self.setPos(pos)
		if quat: self.setQuat(quat)
		
		self.hpr = self.nodePath.getHpr()
		
	def selectionCallback(self, character, direction):
		print "DOOR SELECTED"
		if self.state == "locked" and self.keyCode in character.doorKeysSet:
			self.state = "close"
			
		if self.state == "close":
			self.open(self.nodePath.getRelativeVector(base.cam, Vec3(0, 1, 0).getY()))
		elif self.state == "open":
			self.close()
	
	def update(self, stepSize):
		quat = self.nodePath.getQuat(render)
		pos = self.nodePath.getPos(render)
		
		pos += render.getRelativeVector(self.nodePath, Vec3(-0.5025, 0, 0))
		
		self.geom.setPosition(pos)
		self.geom.setQuaternion(quat)
	
		if self.visualization:
			self.visualization.setQuat(quat)
			self.visualization.setPos(pos)
	
	def close(self):
		self.newH = 0.0
		closeInterval = LerpHprInterval(self.nodePath, self.speed, self.hpr)
		Sequence(
			Func(self.changeState, "closing"),
			closeInterval,
			Func(self.changeState, "close"),
		).start()
		
	def open(self, dir):
		if dir.getY() > 0:
			newH = -85.0
		else:
			newH = 85.0
		self.newH = newH
		
		newH += self.nodePath.getH()
		
		openInterval = LerpHprInterval(self.nodePath, self.speed, Vec3(newH, 0, 0))
		Sequence(
			Func(self.changeState, "opening"),
			openInterval,
			Func(self.changeState, "open"),
		).start()
		
	def changeState(self, newState):
		self.state = newState
	
