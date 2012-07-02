from direct.interval.IntervalGlobal import *

from system.odeWorldManager import *
from kcc import kinematicCharacterController

import platform

"""
Special case of the KCC meant for the Player.

Supports:
	1) FPP camera with 3 ways of handling the mouse movement,
	2) Picking up objects,
	3) Using objects, held and in the world,
	4) Sitting on chairs,
	5) Flashlight

It's undergone some code cleanup for 1.2.0 and it's now easier to set the camera height.
Additionally, I've added an animation for camera movement so it's finally smooth
when going from standing to crouching and back and when walking steps.
"""
class playerController(kinematicCharacterController, DirectObject):
	def __init__(self, game, charNP=None):
		kinematicCharacterController.__init__(self, game)
		self.name = "Player"
		
		"""
		See the KCC file
		"""
		self.setCapsuleData(1.85, 0.8, 0.3, 0.35)
		
		"""
		Set how high above the character's feet the camera is while standing and while crouching.
		"""
		self.setCameraHeight(1.60, .75)
		self.cameraHeight = self.crouchCameraHeight
		
		self.setMovementSpeeds(2.6, 5.2, 6.5)
		
		self.isSitting = False
		self.isDisabled = False
		
		"""
		This holds the camera smoothing animation
		"""
		self.cameraSteppingAnim = None
		
		"""
		I've decided to split that stuff into a couple more methods to make the code more manageable.
		"""
		self.setupTriggerInput()
		self.setupAiming()
		
		self.setupMouseLook()
		self.createFlashlight()
		
		"""
		The place for the held item. You'll probably want to replace this
		with a more sophisticated inventory system.
		"""
		self.heldItem = None
		
		"""
		Set one of two main variants of handling object carrying.
		See placeObjectInFrontOfCamera method to see what this is for.
		"""
		self.jiggleHeld = True
		
	def setMovementSpeeds(self, walkSpeed, runSpeed, jumpSpeed):
		self.walkSpeed = walkSpeed
		self.runSpeed = runSpeed
		self.jumpSpeed = jumpSpeed
	
	def setupAiming(self):
		self.aimRay = rayObject(self.map)
		self.aimRay.setRayGeom(2.5, [Vec3(0, 0, 0), Vec3(0, 1.0, 0)])
		self.aimRay.collisionCallback = self.aimRayCollision
		self.aimRay.setCatColBits("kccAimRay")
		self.map.worldManager.addObject(self.aimRay)
		
		self.aimed = None
		self.aimCollisions = []
	
	def createFlashlight(self):
		lens = PerspectiveLens()
		lens.setFov(75.0)
		self.flashlight = Spotlight("self.flashlight")
		self.flashlight.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
		self.flashlight.setLens(lens)
		self.flashlightNP = base.cam.attachNewNode(self.flashlight)
		self.flashlightState = False
	
	def setupTriggerInput(self):
		self.triggerInput = DirectObject()
		self.triggerInput.accept("ladder_trigger_enter", self.setFly, [True])
		self.triggerInput.accept("ladder_trigger_exit", self.setFly, [False])
		
	def setupMouseLook(self):
		self.mouseLookSpeedX = 8.0
		self.mouseLookSpeedY = 1.2
		
		self.mousePrevX = 0.0
		self.mousePrevY = 0.0
		
		self.hCounter = 0
		self.h = 0.0
		self.p = 0.0
		self.pCounter = 0
		self.printMouseLook = False
		
		base.disableMouse()
	
	def setCameraHeight(self, walkCameraHeight = None, crouchCameraHeight = None):
		if walkCameraHeight is None:
			self.walkCameraHeight = self.capsuleWalkLength
		else:
			self.walkCameraHeight = walkCameraHeight
			
		if crouchCameraHeight is None:
			self.crouchCameraHeight = self.capsuleCrouchLength
		else:
			self.crouchCameraHeight = crouchCameraHeight
		
		return True
	
	def destroy(self):
		self.flashlightNP.remove()
		self.flashlightNP = None
		self.flashlight = None
		
		self.disableInput()
		self.disable()
		self.triggerInput.ignoreAll()
		
		del self.flashlightNP
		del self.flashlight
		del self.triggerInput
		
		kinematicCharacterController.destroy(self)
	
	def sitOnChair(self, chair):
		chairQuat = chair.getNodePath().getQuat(render)
		newPos0 = chair.getNodePath().getPos(render) + chairQuat.xform(Vec3(0, 0.2, 1.0))
		newPos1 = chair.getNodePath().getPos(render) + chairQuat.xform(Vec3(0, 0.0, 0.7))
		newHpr = chair.getNodePath().getHpr(render)
		newHpr[1] = -20.0
		
		startHpr = base.cam.getHpr(render)
		startHpr[0] = self.getQuat().getHpr().getX()
		
		Sequence(
			Func(self.disableInput),
			Func(self.setSitting, chair),
			LerpPosHprInterval(base.cam, 1.0, newPos0, newHpr, None, startHpr),
			LerpPosInterval(base.cam, .5, newPos1),
			Func(self.enableInput),
		).start()
		
	def standUpFromChair(self):
		chairQuat = self.isSitting.getNodePath().getQuat(render)
		newPos0 = self.isSitting.getNodePath().getPos(render) + chairQuat.xform(Vec3(0, 0.2, 1.0))
		newPos1 = self.getPos()
		newPos1.setZ(newPos1.getZ()+self.cameraHeight)
		newHpr = self.getQuat().getHpr()
		
		chair = self.isSitting
		
		Sequence(
			Func(self.setSitting, None),
			LerpPosInterval(base.cam, 0.3, newPos0),
			LerpPosHprInterval(base.cam, 0.5, newPos1, newHpr),
			Func(self.enable),
			Func(chair.setState, "vacant")
		).start()
		
	def setSitting(self, chair):
		if chair:
			self.disable()
		self.isSitting = chair
		
	def disable(self):
		self.isDisabled = True
		self.geom.disable()
		self.footRay.disable()
		
	def enable(self):
		self.footRay.enable()
		self.geom.enable()
		self.isDisabled = False
	
	"""
	Enable/disable flying.
	Changed in 1.2.0
	"""	
	def setFly(self, value, object, trigger):
		if object is not self:
			return
		if value:
			self.state = "fly"
		else:
			self.state = "ground"
	
	def toggleFlashlight(self):
		print "TOGGLE FLASHLIGHT"
		if not self.flashlightState:
			render.setLight(self.flashlightNP)
			self.flashlightState = True
		else:
			render.clearLight(self.flashlightNP)
			self.flashlightState = False
	
	"""
	Enable mouse-move.
	"""
	def enableMovement(self):
		props = WindowProperties()
		
		"""
		!!IMPORTANT!!
		
		I advice using MRelative mode for more fluent mouselook.
		"""
		props.setMouseMode(WindowProperties.MRelative)
		props.setCursorHidden(True)
		
		mouse = base.win.getPointer(0)
		self.mousePrevX = mouse.getX()
		self.mousePrevY = mouse.getY()
		
		base.win.requestProperties(props)
		
		"""
		I found the method now tagged "Linux" to cause problems on Windows,
		so I wrote a different method for this system.
		"""
		if platform.system() == "Windows":
			taskMgr.add(self.updateMouseWindows, "updateMouse")
		elif platform.system() == "Linux":
			taskMgr.add(self.updateMouseLinux, "updateMouse")
	
	def enableInput(self):
		print "Enabling player input"
		self.forwardToken = inputState.watchWithModifiers("forward", "w")
		self.backwardToken = inputState.watchWithModifiers("backward", "s")
		self.strafeLToken = inputState.watchWithModifiers("strafeLeft", "a")
		self.strafeRToken = inputState.watchWithModifiers("strafeRight", "d")
		self.runToken = inputState.watchWithModifiers("run", "shift")
		self.crouchToken = inputState.watchWithModifiers("crouch", "control")
		
		self.accept("space", self.jump)
		
		self.accept("mouse1", self.useHeld)
		self.accept("mouse1-up", self.useHeldStop)
		self.accept("mouse3", self.useAimed)
		self.accept("mouse2", self.dropHeld)
		
		self.accept("f", self.toggleFlashlight)
		
	def disableMovement(self):
		taskMgr.remove("updateMouse")
		
		props = WindowProperties()
		props.setMouseMode(WindowProperties.MAbsolute)
		props.setCursorHidden(False)
		
		base.win.requestProperties(props)
		
	def disableInput(self):
		print "Disabling player input"
		self.ignoreAll()
		self.forwardToken.release()
		self.backwardToken.release()
		self.strafeLToken.release()
		self.strafeRToken.release()
		self.runToken.release()
		self.crouchToken.release()
		
	"""
	Pick up the item we're aiming at.
	"""
	def pickUpItem(self, object):
		if self.heldItem is None:
			self.heldItem = object
			return True
		return False
	
	"""
	use/start using the item we're holding.
	"""
	def useHeld(self):
		if self.heldItem is not None:
			self.heldItem.useHeld()
	
	"""
	stop using the item we're holding.
	"""
	def useHeldStop(self):
		if self.heldItem is not None:
			self.heldItem.useHeldStop()
	
	"""
	Drop the item we're holding.
	"""
	def dropHeld(self):
		if self.heldItem is None:
			return False
			
		self.placeObjectInFrontOfCamera(self.heldItem)
		
		dir = render.getRelativeVector(base.cam, Vec3(0, 1.0, 0))
		pos = base.cam.getPos(render)
		heldPos = self.heldItem.geom.getPosition()
		
		"""
		This raycast makes sure we don't drop the item when there's anything
		between the character and the item (like a wall).
		"""
		exclude = [self.geom, self.heldItem.geom]
		l = (pos - heldPos).length()
		closestEntry, closestGeom = self.map.worldManager.doRaycastNew("kccEnvCheckerRay", l, [pos, dir], exclude)
		
		if not closestEntry is None:
			return False
		
		self.heldItem.drop()
		self.heldItem = None
	
	"""
	Drop and then throw the held item in the direction we're aiming at.
	"""
	def throwHeld(self, force):
		if self.heldItem is None:
			return False
		
		held = self.heldItem
		self.dropHeld()
		
		quat = base.cam.getQuat(render)
		held.getBody().setForce(quat.xform(Vec3(0, force, 0)))
		
		held = None
	
	"""
	The using objects in the world mechanics has changed a lot in version 1.2.0
	I no longer use an in-place raycast. Instead, I incorporated the same mechanics
	of collecting hits as in the guns class.
	"""
	def aimRayCollision(self, entry, object1, object2):
		if not entry.getNumContacts():
			return
		if object2 is self:
			return
		
		distance = (entry.getContactPoint(0) - base.cam.getPos(render)).length()
		self.aimCollisions.append([object2, distance])
	
	def updateAimCollisions(self, pos, quat):
		self.aimRay.geom.set(pos, quat.xform(Vec3(0, 1, 0)))
		
		if not self.aimCollisions:
			self.aimed = None
			return
		
		closest = self.aimCollisions[0]
		for entry in self.aimCollisions:
			if entry[1] < closest[1]:
				closest = entry
		
		self.aimed = closest[0]
		
		self.aimCollisions = []
		print "player -> updateAimCollisions" + str(self.aimCollisions)
	
	def useAimed(self):
		if not self.aimed:
			return False
		
		dir = render.getRelativeVector(base.cam, Vec3(0, 1, 0))
		self.aimed.selectionCallback(self, dir)
		
		return True
	
	"""
	Set camera to correct height above the center of the capsule
	when crouching and when standing up.
	"""
	def crouch(self):
		kinematicCharacterController.crouch(self)
		self.cameraHeight = self.crouchCameraHeight
	
	def crouchStop(self):
		"""
		Only change the camera's placement when the KCC allows standing up.
		See the KCC to find out why it might not allow it.
		"""
		if kinematicCharacterController.crouchStop(self):
			self.cameraHeight = self.walkCameraHeight
			
	def jump(self):
		kinematicCharacterController.jump(self)
	
	"""
	This method is used when carrying objects around.
	"""
	def placeObjectInFrontOfCamera(self, object, curve = None):
		"""
		Whether to disable the geom's collisions when carrying an object or not.
		"""
		disable = False
		
		"""
		Whether to curve the geom's movement when carrying an object or not.
		That is, whether to place the object directly in front of the camera, or
		move it just up and down on one axis relative to the capsule.
		
		The way I use this is as follows:
		
		For objects like boxes or balls, that they player can carry around and stack I disable curveUp.
		This makes it easier to stack boxes for example.
		
		For objects like granades, which are meant to be thrown, I enable curveUp.
		This allows the object to be thrown from the center of the camera when
		looking up.
		
		NOTE that there's no curve down. That's because it would make the player stand
		on the carried object.
		"""
		if curve is None:
			if object.pickableType == "carry":
				curveUp = False
				disable = False
			else:
				curveUp = True
				disable = True
		
		geom = object.geom
		body = object.body
		
		if disable:
			geom.disable()
			if body:
				body.disable()
		
		camQuat = base.cam.getQuat(render)
		capsuleQuat = self.movementParent.getQuat(render)
		
		"""
		Dividing this allows me to control how high the object goes when looking up.
		Experiment with this value.
		"""
		z = camQuat.getHpr()[1]/30
		if z < -1.3:
			z = -1.3
		
		if curveUp:
			zoffset = 0.7
		else:
			zoffset = 0.3
		
		"""
		Get the current position of the geom for manipulating.
		"""
		currentPos = self.geom.getPosition()
		
		"""
		Place the geom relative to the capsule or relative to the camera depending
		on curveUp and z value.
		"""
		if curveUp and z >= 0.0:
			newPos = currentPos + camQuat.xform(Vec3(0.0, 1.3 + (0.35 * z), zoffset - (0.2 * z)))
		else:
			newPos = currentPos + capsuleQuat.xform(Vec3(0.0, 1.3, zoffset + z))
			
		
		"""
		This is the "jiggling" mechanics. When the object is kept enabled, this controlls
		whether and how the other objects and the static environment affect the held object.
		
		If jiggling is enabled, you will notice that the held item reacts to collisions with
		other objects. Note however that it doesn't prevent the held object from penetrating
		other objects, so it might look a little strange.
		
		I wrote it because it looks funny. You can compare it to the Wobbly windows in Compiz.
		"""
		if self.jiggleHeld and body and body.getLinearVel().length() > 0.0:
			newPos += body.getLinearVel() * self.map.worldManager.stepSize * 4.0
		
		geom.setPosition(newPos)
		geom.setQuaternion(capsuleQuat)
		
		"""
		Make sure to disable the gravity for the held object's body
		"""
		if body:
			body.setGravityMode(0)
			body.setPosition(newPos)
			body.setQuaternion(capsuleQuat)
	
	
	"""
	Three mouse look methods. All of them are optimized for as fluent movement as I could get.
	
	The updateMouseAbsolute is the one meant for systems where MRelative is not supported.
	Otherwise use one of the other two.
	
	I have no idea which one would work for MacOSX.
	"""
	def updateMouseLinux(self, task=None):
		mouse = base.win.getPointer(0)
		x = mouse.getX() - self.mousePrevX
		y = mouse.getY() - self.mousePrevY
		
		h = x * (8.0 / 45.0)
		p = y * (1.2 / 4.5)
		
		p = base.cam.getP() - p
		if p < 90.0 and p > -90.0:
			base.cam.setP(p)
			
		self.mouseHandleSitting(h)
		
		self.mousePrevX = mouse.getX()
		self.mousePrevY = mouse.getY()
		
		if task:
			return task.cont
		
	def updateMouseWindows(self, task=None):
		mouse = base.win.getPointer(0)
		x = mouse.getX() - base.win.getXSize()/2
		y = mouse.getY() - base.win.getYSize()/2
		
		h = x * (8.0 / 45.0)
		p = y * (1.2 / 4.5)
		
		p = base.cam.getP() - p
		if p < 90.0 and p > -90.0:
			base.cam.setP(p)
			
		self.mouseHandleSitting(h)
		
		base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2)
		
		if task:
			return task.cont
		
	def updateMouseAbsolute(self, task):
		mouse = base.win.getPointer(0)
		x = mouse.getX() - base.win.getXSize() / 2
		y = mouse.getY() - base.win.getYSize() / 2
		h = 0.0
		p = 0.0
		
		if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
			p = y * (self.mouseLookSpeedY / 10.0)
			h = x * (self.mouseLookSpeedX / 100.0)
			
			if p == 0.0 and self.pCounter < 5:
				p = self.p
				self.pCounter += 1
			else:
				self.pCounter = 0
				self.p = p
			if h == 0.0 and self.hCounter < 5:
				h = self.h
				self.hCounter += 1
			else:
				self.hCounter = 0
				self.h = h
				
		p = base.cam.getP() - p
		if p < 90.0 and p > -90.0:
			base.cam.setP(p)
			
		self.mouseHandleSitting(h)
		
		return task.again
	
	def mouseHandleSitting(self, h):
		if self.isSitting:
			h = base.cam.getH() - h
			if abs(self.isSitting.getNodePath().getH() - h) < 140.0:
				base.cam.setH(h)
		else:
			base.cam.setH(base.cam.getH() - h)
			self.setH(base.cam.getH())
	
		
	def cameraAnimation(self, deltaH):
		base.cam.setZ(deltaH)
	
	def clearCameraAnimation(self):
		self.cameraSteppingAnim.finish()
		self.cameraSteppingAnim = None
	
	"""
	Update the Player Controller specific stuff and the KCC.
	"""
	def update(self, stepSize):
		"""
		I use "forward" for standing up from a chair.
		"""
		if self.isSitting:
			camPos = base.cam.getPos(render)
			camQuat = base.cam.getQuat(render)
			self.updateAimCollisions(camPos, camQuat)
			
			if inputState.isSet("forward"):
				self.standUpFromChair()
			return
		elif self.isDisabled:
			return
		
		# MOVEMENT
		"""
		Handle input. Note that in the main.py file there's this line:
			base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
		It is very important to make sure you can, for example, walk forward,
		strafe and jump at the same time.
		"""
		newLinearVelocity = Vec3(0,0,0)
		
		moveAtSpeed = self.walkSpeed
		if inputState.isSet("run"): moveAtSpeed = self.runSpeed
		
		if inputState.isSet("forward" ): newLinearVelocity[1] = moveAtSpeed
		if inputState.isSet("backward" ): newLinearVelocity[1] = -moveAtSpeed
		if inputState.isSet("strafeLeft"): newLinearVelocity[0] = -moveAtSpeed
		if inputState.isSet("strafeRight"): newLinearVelocity[0] = moveAtSpeed
		
		
		if self.state == "fly":
			self.linearVelocity = base.cam.getQuat(render).xform(newLinearVelocity)
		else:
			self.linearVelocity = self.movementParent.getQuat(render).xform(newLinearVelocity)
		
		if inputState.isSet("crouch"):
			self.crouch()
		else:
			self.crouchStop()
		
		self.currentPos += self.linearVelocity * stepSize
		
		kinematicCharacterController.update(self, stepSize)
		
		# CAMERA
		camPos = self.currentPos + Vec3(0, 0, self.cameraHeight)
		camQuat = base.cam.getQuat(render)
		
		print camPos
		from interpreter import cliClass
		interpreter = cliClass()
		interpreter.sendPos(camPos)
    	
		base.cam.setX(camPos[0])
		base.cam.setY(camPos[1])
		
		if not self.cameraSteppingAnim:
			if self.state == "ground":		
				fromH = base.cam.getPos(render)[2]
				toH = camPos[2]
				
				self.cameraSteppingAnim = Sequence(
					LerpFunc(self.cameraAnimation, fromData = fromH, toData = toH, duration = 0.1),
					Func(self.clearCameraAnimation)
					)
				self.cameraSteppingAnim.start()
			else:
				base.cam.setZ(camPos[2])
		
		self.movementParent.setH(base.cam.getH(render))
		
		# AIMING
		self.updateAimCollisions(camPos, camQuat)
		
		# HELD ITEM
		held = self.heldItem
		if held:
			self.placeObjectInFrontOfCamera(held)
			
			if held.body and held.pickableType == "carry":
				held.body.enable()
				
				held.body.setLinearVel(Vec3(*[0.0]*3))
				held.body.setAngularVel(Vec3(*[0.0]*3))
