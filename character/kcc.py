from system.odeWorldManager import *

"""
The class implementing a Kinematic Character Controller for ODE.

The KCC is the standard approach to character controllers in engines like
PhysX or Havok. Another possible implementation is the Dynamic Character
Controller, but it's much less stable and predictable, and much more inert
than the KCC.

This Kinematic Character Controller implementation has the following features:

1) Movement in 2 dimensions for walking.
2) Movement in 3 dimensions (flying) for walking ladders, swimming etc.
3) Jumping with space awareness:
	3.1) Ceiling-penetration prevention,
	3.2) Automatic crouching when you jump into a space too small for the KCC to stand in,
	3.3) The capsule should never fit into spaces too small for the KCC to stand or crouch in.
4) Walking steps
5) Crouching with space awareness. The KCC never stands up when there's not enough space above it's head.
6) Kinematic and dynamic moving platforms support.

My todo includes integrating it with PandaAI for NPCs.

Note that the KCC doesn't inherit from the kinematicObject class. There was simply no such need.
This also means, that your classes also don't need to inherit from that (or from any *Object class
for that matter) as long as they implement all methods and variables required for WorldManager
to understand them (like objectType variable and collisionCallback method).
"""

class kinematicCharacterController(kinematicObject):
	def __init__(self, map, charNP=None):
		kinematicObject.__init__(self, map)
		"""
		Those values don't really matter, but they need to be here for
		world manager.
		"""
		self.surfaceFriction = 0.0
		self.surfaceBounce = 0.0
		self.surfaceBounceVel = 0.0
		self.surfaceSoftERP = 0.0
		self.surfaceSoftCFM = 0.00001
		self.surfaceSlip = 0.0
		self.surfaceDampen = 2.0
		
		self.geom = None
		self.body = None
		self.objectType = "kinematic"
		
		"""
		Since ver. 1.2.0 it now so happens it supports visualization.
		"""
		self.visualize = False
		
		"""
		FINALLY you can easily set the height, radius and stepping height! Just like that.
		"""
		self.setCapsuleData(1.85, 0.8, 0.3, 0.35)
		
		"""
		Initial values
		"""
		self.capsuleCurrentLength = self.capsuleWalkLength
		self.capsuleCurrentLevitation = self.capsuleWalkLevitation
		self.capsuleCurrentRadius = self.capsuleWalkRadius
		
		"""
		Setup the Capsule for the character
		"""
		self.geom = OdeCappedCylinderGeom(self.map.worldManager.getSpace(), self.capsuleCurrentRadius, self.capsuleCurrentLength)
		
		"""
		Visualization.
		"""
		if self.visualize:
			self.visualization = wireGeom().generate("capsule", radius = self.capsuleCurrentRadius, length = self.capsuleCurrentLength)
			self.visualization.reparentTo(render)
		else:
			self.visualization = None
		
		"""
		Now the movement parent is a nodepath so you can easily animate the KCC. Or parent geometry to the movementParent to make an NPC.
		"""
		self.movementParent = render.attachNewNode("kccMovementParent")
		
		"""
		NOTE the default bitmask name has changed. Actually, the KCC's bitmasks changed quite a lot in 1.2.0 so keep them in mind when reading on.
		"""
		self.setCatColBits("kccCapsule")
		
		"""
		Since 1.2.0 the KCC consists of two capsules instead of one. That's because I need to be able to push stuff around, and when I was doing it
		with just one levitating capsule it fliped the boxes to their side and stepped on them. To prevent that I introduced another capsule
		which covers the whole size of the KCC.
		"""
		self.dynamicCollider = staticObject(self.map)
		self.dynamicCollider.setCapsuleGeom(self.capsuleWalkRadius, self.walkH - self.capsuleWalkRadius * 2.0 - 0.1)
		self.dynamicCollider.setCatColBits("kccDynamicCollider") # It has it's own bitmask. See in the WorldManager file
		self.dynamicCollider.getLinearVel = self.getLinearVel # A hack necessary because this must be a static object (for convenience reasons), however those do not have getLinearVel()
		self.dynamicCollider.objectType = "kinematic" # The second part of the hack. Tricking the World Manager and other objects to see this as a kinematic object. This way I, quite simply, created a compount kinematic object.
		self.map.worldManager.addObject(self.dynamicCollider)
		
		"""
		Setup the Ray, which serves as the character's feet, making sure
		the capsule levitates correctly above the ground.
		
		You might notice a change here comparing to version 0.9. Before,
		the footRay was a "naked" geom, now I operate solely on *Objects.
		"""
		self.footRay = rayObject(self.map)
		self.footRay.objectType = "ray"
		self.footRay.setRayGeom(self.capsuleCurrentLevitation + 0.5, [Vec3(0,0,0), Vec3(0,0,-1)])
		
		"""
		Make sure we grab the collisions from this object.
		"""
		self.footRay.collisionCallback = self.footCollision
		self.footRay.setCatColBits("kccFootRay")
		self.map.worldManager.addObject(self.footRay)
		
		"""
		Another ray, this time upwards. This makes sure we don't penetrate the
		ceiling no matter what, and that we don't stand up when there's not
		enough space to do it.
		"""
		self.envCheckerRay = rayObject(self.map)
		self.envCheckerRay.objectType = "ray"
		self.envCheckerRay.setRayGeom(self.capsuleWalkLength / 2 + self.radius, [Vec3(0, 0, 0), Vec3(0, 0, 1.0)])
		
		"""
		Again, redirect the collision callback to this class.
		"""
		self.envCheckerRay.collisionCallback = self.envCheckerCollision
		self.envCheckerRay.setCatColBits("kccEnvCheckerRay") # In case you haven't noticed, the KCC now has 4 bitmasks
		self.map.worldManager.addObject(self.envCheckerRay)
		
		self.map.worldManager.addObject(self)
		
		"""
		Variables used for movement, jumping and falling.
		"""
		self.linearVelocity = Vec3(0, 0, 0)
		self.jumpStartPos = 0.0
		self.jumpTime = 0.0
		self.jumpSpeed = 0.0
		self.fallStartPos = 0.0
		self.fallSpeed = 0.0
		self.fallTime = 0.0
		
		"""
		State variable which can take one of four values:
		ground, jumping, falling or fly
		"""
		self.state = ""
		
		"""
		Crouching is a special kind of a state. It's not a value of the
		self.state variable because you can, for example, fall while crouching.
		"""
		self.isCrouching = False
		
		"""
		This is used by stability insurance.
		"""
		self.footContactPrevious = None
		self.footContact = None
		self.envCheckerContact = None
		
		"""
		This controls whether this KCC can or cannot use dynamic objects as moving platforms.
		I advice disabling that for NPC's or you'll get funny results.
		"""
		self.dynamicPlatforms = True
		self.noclip = False
	
	"""
	New in method 1.2.0. About time, you say.
	
	This nice method lets you easily set the walk height, the crouch height and the radius of the KCC
	as well as how high steps it'll be able to walk up. It translates those values into the main capsule length,
	radius and levitation.
	"""
	def setCapsuleData(self, walkH, crouchH, stepH, R):
		self.capsuleWalkLength, self.capsuleWalkLevitation, self.capsuleWalkRadius = self.setData(walkH, stepH, R)
		self.capsuleCrouchLength, self.capsuleCrouchLevitation, self.capsuleCrouchRadius = self.setData(crouchH, stepH, R)
		
		self.stepH = stepH
		self.crouchH = crouchH
		self.walkH = walkH
		
		self.radius = R
		
		if self.geom is not None:
			self.geom.setParams(self.capsuleWalkRadius, self.capsuleWalkLength)
			self.dynamicCollider.geom.setParams(self.capsuleWalkRadius, self.walkH - self.capsuleWalkRadius * 2.0 - 0.1)
			self.capsuleCurrentLevitation = self.capsuleWalkLevitation
			
			self.footRay.geom.setLength(self.capsuleWalkLevitation + 0.5)
			self.envCheckerRay.geom.setLength(self.capsuleWalkLength / 2 + self.radius)
		
		return True
	
	"""
	This method is used by the method above.
	"""
	def setData(self, fullH, stepH, R):
		if fullH - stepH <= R * 2.0:
			length = 0.1
			R = (fullH * 0.5) - (stepH * 0.5)
			lev = stepH + R
		else:
			length = (fullH - stepH) - (2.0 * R)
			lev = fullH - (length / 2.0) - R
		
		return length, lev, R
	
	def getCapsuleData(self):
		return self.stepH, self.crouchH, self.walkH, self.radius
	
	def getGeom(self):
		return self.geom
	
	def setCatColBits(self, name):
		self.bitsName = name
		self.geom.setCollideBits(bitMaskDict[name][0])
		self.geom.setCategoryBits(bitMaskDict[name][1])
	
	def destroy(self):
		self.map.removeObject(self)
		
		self.map.worldManager.removeObject(self)
		self.geom.destroy()
		
		self.map.worldManager.removeObject(self.dynamicCollider)
		self.dynamicCollider.destroy()
		
		self.map.worldManager.removeObject(self.footRay)
		self.footRay.destroy()
		
		self.map.worldManager.removeObject(self.envCheckerRay)
		self.envCheckerRay.destroy()
		
		del self.map
		del self.geom
		del self.footRay
		del self.envCheckerRay
		del self.dynamicCollider
		
	def setPos(self, pos):
		self.geom.setPosition(pos)
		self.currentPos = pos
	
	def getPos(self):
		return self.currentPos
	
	"""
	Convenience method for setting the capsule's heading.
	"""
	def setH(self, h):
		quat = self.getQuat()
		hpr = quat.getHpr()
		hpr[0] = h
		quat.setHpr(hpr)
		self.setQuat(quat)
		
	def setQuat(self, quat):
		self.movementParent.setQuat(render, Quat(quat))
		
	def getQuat(self):
		return self.movementParent.getQuat(render)
	
	"""
	Start crouching
	"""
	def crouch(self):
		if not self.isCrouching:
			self.capsuleCurrentLevitation = self.capsuleCrouchLevitation
			self.capsuleCurrentLength = self.capsuleCrouchLength
			self.capsuleCurrentRadius = self.capsuleCrouchRadius
			self.geom.setParams(self.capsuleCurrentRadius, self.capsuleCurrentLength)
			
			self.isCrouching = True
			return True
		else:
			return False
	
	"""
	Stop crouching
	"""
	def crouchStop(self):
		if not self.isCrouching:
			return False
		
		"""
		Did the envCheckerRay detect any collisions? If so, prevent the
		KCC from standing up as there's not enough space for that.
		
		This removes the need for crouch locking triggers.
		"""
		if self.envCheckerContact is not None:
			return False
		
		self.capsuleCurrentLevitation = self.capsuleWalkLevitation
		self.capsuleCurrentLength = self.capsuleWalkLength
		self.capsuleCurrentRadius = self.capsuleWalkRadius
		
		self.geom.setParams(self.capsuleCurrentRadius, self.capsuleCurrentLength)
		
		self.isCrouching = False
		return True
		
	"""
	Handle a collision of the capsule.
	"""
	def collisionCallback(self, entry, object1, object2):
		if self.noclip:
			return False
		
		if not entry.getNumContacts() or object2.objectType in ["trigger", "ray", "ccd"]:
			return False
		
		if object2.objectType != "dynamic":
			prevNormal = None
			
			for i in range(entry.getNumContacts()):
				"""
				Handling a contact of the same normal twice (or more) is almost always pointless.
				It indicates that we're dealing with a trimesh collision, in which
				a separate contact is added for each polygon causing the KCC to flicker
				because the placement correction is applied for every conact with the same
				depth.
				
				This code filters the redundant contacts making the KCC collide more
				with the planes the polygons reside on, rather then the polygons themselves.
				
				I initially tried to just divide the depth by the number of contacts but
				that did not work. The KCC just went through many objects because that method
				didn't take into account that there can be different normals among contacts.
				
				This sollutions proves relatively stable.
				"""
				geom = entry.getContactGeom(i)
				normal = geom.getNormal()
				
				if prevNormal == normal:
					continue
				prevNormal = normal
				
				point = entry.getContactPoint(i)
				depth = geom.getDepth()
				
				if entry.getGeom1() == self.geom:
					for i in range(3):
						self.currentPos[i] += depth * normal[i]
				else:
					for i in range(3):
						self.currentPos[i] -= depth * normal[i]
				
				"""
				Stop the jump if the KCC hits a ceiling.
				"""
				if normal[2] == -1:
					if self.state == "jumping":
						self.fallStartPos = self.currentPos[2]
						self.fallSpeed = 0.0
						self.fallTime = 0.0
						self.state = "falling"
		return True
	
	"""
	Handle a collision involving the environment checker ray.
	"""
	def envCheckerCollision(self, entry, object1, object2):
		if self.noclip:
			return
		
		if not entry.getNumContacts():
			return
		if object2 is self:
			return
		
		"""
		Get the lowest contact.
		"""
		for i in range(entry.getNumContacts()):
			contact = entry.getContactPoint(i)[2]
			
			if self.envCheckerContact is None or (contact < self.envCheckerContact):
				self.envCheckerContact = contact
	
	"""
	Handle a collision of the foot ray.
	"""
	def footCollision(self, entry, object1, object2):
		if self.noclip:
			return
		
		if not entry.getNumContacts():
			return
		if object2 is self:
			return
		
		for i in range(entry.getNumContacts()):
			contact = entry.getContactPoint(i)[2]
			
			if self.footContact is None or (contact > self.footContact[0]):
				self.footContact = [contact, object2]
	
	"""
	UPDATE THE KCC
	"""
	def update(self, stepSize):
		if self.noclip:
			self.state = "fly"
		
		"""
		Since 1.2.0 this code is a lot cleaner. Also, all hardcoded stuff was removed.
		"""
		capsuleCurrentElevation = None
		
		if self.footContact is not None:
			capsuleCurrentElevation = self.geom.getPosition()[2] - self.footContact[0]
		
		if self.envCheckerContact is not None:
			spaceHeight = self.envCheckerContact - self.currentPos[2]
			
			if spaceHeight < self.walkH and capsuleCurrentElevation < self.capsuleCurrentLevitation:
				self.crouch()
				
			elif spaceHeight < self.crouchH and capsuleCurrentElevation < self.capsuleCrouchLevitation:
				self.footContact = self.footContactPrevious
		
		# Process possible states
		if self.state == "fly" and self.footContact and capsuleCurrentElevation < self.capsuleCurrentLevitation and self.linearVelocity.getZ() < 0:
			self.currentPos[2] = self.footContact[0]
			
		elif self.state == "fly":
			pass
			
		elif self.state == "jumping":
			self.currentPos[2] = self.processJump(self.currentPos, stepSize, self.footContact)
		
		elif capsuleCurrentElevation is None:
			self.currentPos = self.fall(self.currentPos, stepSize, self.footContact)
			
		elif capsuleCurrentElevation > self.capsuleCurrentLevitation + 0.01 and capsuleCurrentElevation < self.capsuleCurrentLevitation + 0.65 and self.state == "ground":
			self.currentPos = self.stickToGround(self.currentPos, stepSize, self.footContact)
		
		elif capsuleCurrentElevation > self.capsuleCurrentLevitation + 0.01:
			self.currentPos = self.fall(self.currentPos, stepSize, self.footContact)
			
		elif capsuleCurrentElevation <= self.capsuleCurrentLevitation + 0.01:
			self.currentPos = self.stickToGround(self.currentPos, stepSize, self.footContact)
		
		"""
		NEW IN 1.2.0
		
		This code allows the KCC to be carried by moving kinematic and dynamic objects.
		"""
		if self.footContact is not None:
			if self.footContact[1].objectType == "kinematic":
				platformSpeed = self.footContact[1].getLinearVel()
				self.currentPos += platformSpeed * self.map.worldManager.stepSize
			elif self.footContact[1].objectType == "dynamic" and self.dynamicPlatforms:
				platformSpeed = self.footContact[1].getLinearVel()
				self.currentPos[0] += platformSpeed[0] * self.map.worldManager.stepSize
				self.currentPos[1] += platformSpeed[1] * self.map.worldManager.stepSize
		
		# MOVE THE KCC
		self.movementParent.setPos(render, self.currentPos)
		
		self.dynamicCollider.setPos(self.currentPos + Vec3(0, 0, self.walkH * 0.5))
		
		# Put the KCC elements on their new positions
		newElementsPos = Vec3(self.currentPos)
		newElementsPos[2] += self.capsuleCurrentLevitation
		
		self.geom.setPosition(newElementsPos)
		self.envCheckerRay.setPos(newElementsPos)
		if self.visualization:
			self.visualization.setPos(newElementsPos)
		
		rayPos = Vec3(newElementsPos)
		self.footRay.setPos(rayPos)
		
		self.footContactPrevious = self.footContact
		self.footContact = None
		self.envCheckerContact = None
	
	def getLinearVel(self):
		"""
		This is correct. For collisions with other objects the KCC must have such function,
		but it shouldn't really return any other value.
		"""
		return Vec3(0, 0, 0)
		
	"""
	METHODS FOR PROCESSING STATES
	
	All were changed for 1.2.0
	"""
	def processJump(self, newPos, stepSize, footContact):
		self.jumpTime += stepSize
		
		self.fallSpeed = self.jumpSpeed * self.jumpTime + (-9.81) * (self.jumpTime) ** 2
		
		np = self.jumpStartPos + self.fallSpeed
		
		if footContact is not None and np <= footContact[0]:
			self.state = "ground"
			return footContact[0]
		else:
			return np
		
	def stickToGround(self, newPos, stepSize, footContact):
		self.state = "ground"
		
		if self.fallSpeed:
			self.fallCallback(self.fallSpeed)
		self.fallSpeed = 0.0
		
		newPos[2] = footContact[0]
		
		return newPos
		
	def fall(self, newPos, stepSize, footContact):
		if self.state != "falling":
			self.fallStartPos = self.currentPos[2]
			self.fallSpeed = 0.0
			self.fallTime = 0.0
			self.state = "falling"
		else:
			self.fallTime += stepSize
			self.fallSpeed = (-9.81) * (self.fallTime) ** 2
		newPos[2] = self.fallStartPos + self.fallSpeed
		return newPos
	
	"""
	This is called when the KCC hits the ground after a fall.
	Here you can put health related stuff.
	"""
	def fallCallback(self, speed):
		print "A character has hit the ground with speed:", speed
	
	def setSpeed(self, x, y):
		self.speed[0] = x
		self.speed[1] = y
	
	"""
	Start a jump
	"""
	def jump(self):
		if self.state != "ground":
			return
		self.jumpStartPos = self.currentPos[2]
		self.jumpTime = 0.0
		self.state = "jumping"
		###print "JUMP"
