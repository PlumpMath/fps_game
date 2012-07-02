from pandac.PandaModules import Point3, Vec3
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject

from system.odeWorldManager import *
from inventory import pickableObject

import random

"""
A general class for a firearm.

Uses raycasting, doesn't currently support projectiles, so you cannot
has rocket launchers with this.

By default it acts as a semi-automatic pistol, but supports shotgun
and automatic gun functionality as well. You can even make an automatic
shotgun with it too.

It currently doesn't support inaccuracy OOTB -- the hit spot is always
in the middle of the screen for single-hit-point weapons (!shotguns).

NOTE:

This implementation is probably a little unusual. Since ODE doesn't support
typpical RayCasting like PhysX or Bullet do, I needed to trade accuracy for
performance. Instead of shooting a ray at the very moment you press the trigger
and getting the collisions at that very frame, I keep the rays up all time,
and update them once a simulation pass, so they may not reflect the most
up to date position of the mouse.

While I do have the doRaycast function in odeWorldManager, it's not fast enough
to handle shooting (especially with many characters and/or rifles/shotguns).
The method I used works a lot better for ODE, but for very fast shooters
it might be not enough.
"""
class gun(pickableObject, DirectObject):
	def __init__(self, name="handgun", weight=0.630):
		pickableObject.__init__(self, name, weight)
		
		self.pickableType = "pocket"
		
		self.icon = "./graphics/pickableIcons/pistol.png"
		
		self.modelPath = "./graphics/models/pistol.egg"
		self.geomSize = (0.031, 0.217, 0.129)
		
		"""
		Is it automatic or semi-automatic?
		"""
		self.automatic = False
		
		"""
		How far do you want the bullets to go?
		"""
		self.effectiveRange = 300.0
		
		"""
		Rate of Fire for automatic weapons.
		"""
		self.autoROF = 250.0
		
		"""
		Used for ROF, more on that in the update method.
		"""
		self.autoAccumulator = 0.0
		
		"""
		Number of rays to search for hits with. This basically
		translates to this: If it's more than one, you have a shotgun.
		It it's one -- a pistol or a rifle.
		"""
		self.aimRaysNum = 1
		
		"""
		Holds aim rays.
		"""
		self.aimRays = []
		
		"""
		If you have more than one aim ray, then here you can set how
		dispersed they're going to be.
		"""
		self.shotgunDispersion = 0.2
		
		"""
		Are we shooting ATM?
		"""
		self.shooting = False
		
		"""
		Contains the hits.
		"""
		self.aimCollisions = []
	
	"""
	The callback for aim ray collisions.
	"""
	def aimCollision(self, entry, object1, object2):
		"""
		No point hitting triggers or ccd helpers.
		"""
		if object2.objectType in ["trigger", "ccd"]:
			return
		
		"""
		So we don't shoot ourselves.
		"""
		if object2 is self.owner:
			return
		
		"""
		Append the hit to the list.
		"""
		self.aimCollisions.append([entry, object2])
	
	def destroy(self):
		for ray in self.aimRays:
			self.map.worldManager.removeObject(ray)
			ray.destroy()
		del self.aimCollisions
		del self.aimRays
		pickableObject.destroy(self)
		self.ignoreAll()
	
	"""
	Create the requested number of aim rays.
	"""
	def createAimRays(self):
		for i in range(self.aimRaysNum):
			self.createAimRay()
	
	"""
	Create a single aim ray.
	"""
	def createAimRay(self):
		ray = rayObject(self.map)
		ray.objectType = "ray"
		ray.setRayGeom(self.effectiveRange, [Vec3(0,0,0), Vec3(0,0,-1)])
		ray.collisionCallback = self.aimCollision
		
		self.map.worldManager.addObject(ray)
		self.aimRays.append(ray)
	
	def destroyAimRays(self):
		for ray in self.aimRays:
			self.map.worldManager.removeObject(ray)
			ray.destroy()
		self.aimRays = []
		self.aimCollisions = []
	
	def selectionCallback(self, character, direction):
		pickableObject.selectionCallback(self, character, direction)
		
		"""
		Create the rays when we pick up the gun. No need having them around all the time.
		
		NOTE: In my game, I actually create the rays when the Player withdraws the gun
		from the inventory, but the actual usage depends on application's design.
		"""
		self.createAimRays()
	
	def drop(self):
		"""
		Destroy the rays when we drop the gun.
		"""
		self.destroyAimRays()
		pickableObject.drop(self)
	
	def useHeld(self):
		"""
		Start shooting...
		"""
		self.shooting = True
		return True
	
	def useHeldStop(self):
		"""
		Stop shooting an automatic weapon.
		Semi automatic weapons stop shooting by themselves, right after
		one update pass.
		"""
		if self.automatic:
			self.stopShooting()
		return
	
	def shoot(self, dir):
		"""
		Process the collected hits.
		"""
		for entry, object in self.aimCollisions:
			p = entry.getContactPoint(0)
			if object.body:
				object.body.enable()
				object.body.addForceAtPos(dir*(10**2), p)
	
	def stopShooting(self):
		"""
		Stop shooting and clear the collisions accumulator.
		"""
		self.shooting = False
		self.autoAccumulator = 0.0
		
	def update(self, stepSize):
		pickableObject.update(self,stepSize)
		
		if not self.aimRays:
			self.aimCollisions = []
			return
		
		"""
		Only process hits if the gun is picked up.
		"""
		if self.owner:
			"""
			Get the desired position and direction of the aim ray/s.
			
			NOTE that currently there's only support for Player (camera)
			and not NPCs. Supports for NPCs will come in the next major version.
			"""
			pos = base.cam.getPos(render) + render.getRelativeVector(base.cam, Vec3(0, 0.8, 0))
			dir = render.getRelativeVector(base.cam, Vec3(0, 1.0, 0))
			
			"""
			Handle one ray differently than multiple rays.
			"""
			if self.aimRaysNum == 1:
				"""
				Just set it to aim right at the center of the screen.
				"""
				self.aimRays[0].geom.set(pos, dir)
			else:
				for ray in self.aimRays:
					"""
					Scatter the rays within the limits set by the shotgunDispersion variable.
					"""
					x = random.uniform(-self.shotgunDispersion, self.shotgunDispersion)
					z = random.uniform(-self.shotgunDispersion, self.shotgunDispersion)
					
					"""
					Tweak the direction to take the random values into account.
					"""
					rayDir = Vec3(dir)
					rayDir[0] += x
					rayDir[2] += z
					
					"""
					Position the ray.
					"""
					ray.geom.set(pos, rayDir)
			
			"""
			Handle automatic weapons.
			"""
			if self.automatic and self.shooting:
				"""
				If this is the first frame we're self.shooting == True,
				shoot once and then continue processing.
				"""
				if self.autoAccumulator == 0.0:
					self.shoot(dir)
				
				"""
				Add the rate-of-fire to the accumulator.
				"""
				self.autoAccumulator += self.autoROF
				
				"""
				Get the ROF per second
				"""
				currentROF = 1.0/self.autoAccumulator
				
				"""
				Call shoot method as many times as shots fitting in the
				simulation time step.
				
				That's what the accumulator is for -- thanx to that,
				the speed of shooting depends on values set, not on
				the simulation's update rate.
				"""
				if currentROF < stepSize:
					for i in range(int(stepSize / currentROF)):
						self.shoot(dir)
					self.autoAccumulator = 0.0
			
				"""
				Handle semi automatic shooting.
				"""
			elif self.shooting:
				self.shoot(dir)
		
		"""
		If semi-automatic, make sure to shoot only once.
		"""
		if not self.automatic:
			self.stopShooting()
		
		"""
		Clear aim collisions before the next frame.
		"""
		self.aimCollisions = []

"""
Automatic rifle.
"""
class assaultRifle(gun):
	def __init__(self):
		gun.__init__(self, "rifle", 3.82)
		
		self.icon = "./graphics/pickableIcons/rifle.png"
		
		self.modelPath = "./graphics/models/rifle.egg"
		self.geomSize = (0.049, 0.870, 0.218)
		
		self.automatic = True
		
		self.autoROF = 20.0

"""
A shotgun with 10 rays and 0.3 maximum dispersion.
"""
class shotgun(gun):
	def __init__(self):
		gun.__init__(self, "shotgun", 3.82)
		
		self.icon = "./graphics/pickableIcons/shotgun.png"
		
		self.modelPath = "./graphics/models/shotgun.egg"
		self.geomSize = (0.09, 0.904, 0.301)
		
		self.shotgunDispersion = 0.3
		self.aimRaysNum = 10
