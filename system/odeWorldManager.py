import pdb
import math

from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

from debugVisODE import wireGeom

"""
This is a convenient way of handling the most tedious and powerful part
of ODE -- the bitmasks that control what collides with what.

The previous approach to this was not automated so I finally decided to introduce
something that doesn't require bit-wise calculations done by hand.

This method allows you to easily add new objects without the need for any math.
All you need to pass to the addMask method is the new set's name, a
list of category names it's meant to collide with and, optionally, you can
force it to use a specific category mask.

Note that if you want to keep objects in separate categories, then you
won't be able to use more than 32 different types of objects. That's how it
was intended by ODE developers (according to the manual) and that's how this
works. However, you can force the new mask to use a certain category, although
that might lead to unexpected results when you forget about you did that. So
use with caution.

Note that it's best to prevent the individual parts of the static environment
from colliding with each other, using bit masks. While the World Manager does
make sure there's not real collision handling between them, there's still
a little work done by it (in Python) making the whole collision detection
visibly slower for complex environments. This overhead doesn't take place
when you set the bitmasks like the "environment" below, because then the
collision is droped on the ODE side, before even getting to my code.
"""
bitMaskDict = {}

def addMask(name, collide, forceCategory = None):
	if forceCategory is None:
		newCat = BitMask32(0b1)
		newCat = newCat << len(bitMaskDict)
	else:
		newCat = forceCategory
	
	newCol = BitMask32(0b0)
	
	for dictName in collide:
		if dictName == "self":
			newCol = newCol | newCat
			continue
		
		cat, col = bitMaskDict[dictName]
		newCol = newCol | cat
	
	bitMaskDict[name] = newCat, newCol
	
addMask("environment", [])
addMask("pickable", ["self", "environment"])

addMask("kccCapsule", ["self", "environment"])
addMask("kccFootRay", ["environment", "pickable"])
addMask("kccEnvCheckerRay", ["environment", "pickable"])
addMask("kccAimRay", ["pickable"])
addMask("kccDynamicCollider", ["pickable"])

addMask("charTrigger", ["kccCapsule"])

"""
The basic physical object in this framework. It represents static geometry
and is meant to be used for environment.

More complex objects inherit from this one.
"""
class physicalObject(object):
	def __init__(self, map):
		"""
		A map class instance. See map.py
		"""
		self.map = map
		
		"""
		Node Path, graphical representation for this object
		"""
		self.nodePath = None
		
		"""
		OdeGeom for collision detection
		"""
		self.geom = None
		
		"""
		In case of physicalObject and staticObject this will stay None,
		but it aids the world manager's readability to keep it here.
		"""
		self.body = None
		
		"""
		Shape visualization geom. Currently only Box can be visualized.
		"""
		self.visualization = None
		
		"""
		Object type for World Manager
		
		The possible values* are:
			- static
			- kinematic
			- dynamic (no distinction between ccd and no-ccd)
			- ray
			- trigger (note that previously there was an isTrigger variable)
			- ccd (ccd helper object)
			
		(* that's those my code understands by default,
		feel free to add more)
		"""
		self.objectType = "static"
		
		self.pos = None
		self.quat = None
		
		"""
		Name of the bit masks used for this object.
		"""
		self.bitsName = ""
		
		"""
		Whether to visualize this object ore not.
		"""
		self.visualize = False
		
	def getGeom(self):
		return self.geom
	
	
	def disable(self):
		if self.geom: self.geom.disable()
		if self.body: self.body.disable()
		
	def enable(self):
		if self.geom: self.geom.enable()
		if self.body: self.body.enable()
	
	"""
	Collision and Selection Callbacks, functionality previously
	implemented in the now removed OdeGeomData class.
	"""
	def collisionCallback(self, *args):
		return
	
	def selectionCallback(self, *args):
		return
	
	"""
	Set a custom geom (as in, not created by this class).
	"""
	def setGeom(self, geom):
		self.geom = geom
		
	def getNodePath(self):
		return self.nodePath
		
	"""
	Set the Node Path for this Object's rendering
	
	Model attribute can be a string, containing a path to the model's egg,
	or a nodepath.
	
	Parent indicates the new parent for this node.
	"""
	def setNodePath(self, model, parent=None, scale=1.0, pos=None):
		"""
		Load the model using it's name or wrap around a passed nodepath
		"""
		if isinstance(model, basestring):
			self.nodePath = loader.loadModel(model)
		else:
			self.nodePath = model
		
		self.nodePath.setScale(scale)
		
		if pos:
			self.setPos(pos)
		
		if parent is None:
			pass
		elif parent == "detach":
			self.nodePath.detachNode()
		else:
			self.nodePath.reparentTo(parent)
		
	def detachNode(self):
		self.nodePath.detachNode()
	
	def synchPosQuatToNode(self):
		if self.nodePath:
			self.geom.setPosition(self.nodePath.getPos(render))
			self.geom.setQuaternion(self.nodePath.getQuat(render))
	
	def setPos(self, pos=None):
		if pos is None:
			pos = self.nodePath.getPos(render)
			self.geom.setPosition(pos)
		else:
			if self.nodePath:
				self.nodePath.setPos(render, pos)
			self.geom.setPosition(pos)
		self.pos = pos
		
		if self.visualization:
			self.visualization.setPos(pos)
			
	def getPos(self):
		return self.geom.getPosition()
	
	def getQuat(self):
		return self.geom.getQuaternion()
	
	def setQuat(self, quat=None):
		if quat is None:
			quat = self.nodePath.getQuat(render)
			self.geom.setQuaternion(quat)
		else:
			if self.nodePath:
				self.nodePath.setQuat(render, quat)
			self.geom.setQuaternion(quat)
		self.quat = quat
		
		if self.visualization:
			self.visualization.setQuat(quat)
	
	"""
	Simplified setting collision and category bits for geoms.
	Uses the bitMaskDict dictionary -- see at the begining of this file.
	"""
	def setCatColBits(self, name):
		self.bitsName = name
		self.geom.setCollideBits(bitMaskDict[name][0])
		self.geom.setCategoryBits(bitMaskDict[name][1])
	
	def update(self, stepSize):
		return
		
	def destroy(self):
		self.map.removeObject(self)
		if self.nodePath:
			self.nodePath.remove()
		if self.visualization:
			self.visualization.remove()
		self.geom.destroy()
		del self.visualization
		del self.geom
		del self.nodePath
		del self.map


class staticObject(physicalObject):
	def __init__(self, map):
		physicalObject.__init__(self, map)
		
		"""
		This is the data for handling collisions.
		Previously, this was placed in the OdeGeomData class.
		
		In the future, it might be moved into some other place,
		so that it can be used by many objects, like bitMasks,
		but I didn't want to delay the release because of this.
		"""
		self.surfaceFriction = 0.0
		self.surfaceBounce = 0.3
		self.surfaceBounceVel = 0.5
		self.surfaceSoftCFM = 0.1
		self.surfaceSoftERP = 0.2
		self.surfaceSlip = 0.0
		self.surfaceDampen = 2.0
	
	"""
	Set up an OdeBoxGeom of the given size.
	"""
	def setBoxGeom(self, size):
		self.boxSize = size
		self.geom = OdeBoxGeom(self.map.worldManager.getSpace(), size)
		
		"""
		If visualization is enabled, create the visualization node.
		Note that the visualization technique has changed. Now I use the fantastic code
		by FenrirWolf. If you read this -- big thanks, it's awesome!
		"""
		if self.visualize:
			self.visualization = wireGeom().generate("box", extents = list(self.geom.getLengths() * 0.5))
			self.visualization.reparentTo(render)
			if self.nodePath:
				self.visualization.setPos(self.nodePath.getPos(render))
			
		"""
		If a nodePath is set, get the position and rotation from it
		"""
		self.synchPosQuatToNode()
	
	"""
	Set a box geom from a given model.
	See World Manager class for details.
	"""
	def setBoxGeomFromNodePath(self, node, remove=True):
		size = self.map.worldManager.extractSizeForBoxGeom(node)
		self.setBoxGeom(size)
		if remove:
			node.removeNode()
	
	"""
	Set up an OdeCappedCylinderGeom. New in ver. 1.2
	"""
	def setCapsuleGeom(self, radius, length):
		self.geom = OdeCappedCylinderGeom(self.map.worldManager.getSpace(), radius, length)
		
		if self.visualize:
			self.visualization = wireGeom().generate("capsule", radius = radius, length = length)
			self.visualization.reparentTo(render)
			if self.nodePath:
				self.visualization.setPos(self.nodePath.getPos(render))
			
		self.synchPosQuatToNode()
	
	"""
	Set up an OdeTriMeshGeom from the given node.
	"""
	def setTrimeshGeom(self, model, remove=False):
		if isinstance(model, basestring):
			model = loader.loadModel(model)
		trimeshData = OdeTriMeshData(model, True)
		self.geom = OdeTriMeshGeom(self.map.worldManager.space, trimeshData)
		
		self.synchPosQuatToNode()
		
		if remove:
			model.removeNode()
	
	"""
	Set up an OdeSphereGeom of the given radius.
	"""
	def setSphereGeom(self, radius):
		self.geom = OdeSphereGeom(self.map.worldManager.getSpace(), radius)
		
		if self.visualize:
			self.visualization = wireGeom().generate("sphere", radius = radius)
			self.visualization.reparentTo(render)
			if self.nodePath:
				self.visualization.setPos(self.nodePath.getPos(render))
		
		self.synchPosQuatToNode()
		

"""
The kinematic object class. This type of object it meant to be animated
using Panda's Interval system.

The getLinearVel method makes the moving platforms possible.
"""
class kinematicObject(staticObject):
	def __init__(self, map):
		staticObject.__init__(self, map)
		self.objectType = "kinematic"
		
		self.linearVel = Vec3(0,0,0)
		self.prevPos = Vec3(0,0,0)
	
	"""
	Get linear velocity
	"""
	def getLinearVel(self):
		return self.linearVel
	
	def update(self, stepSize):
		quat = self.nodePath.getQuat(render)
		pos = self.nodePath.getPos(render)
		
		self.linearVel = (pos - self.prevPos) / self.map.worldManager.stepSize
		
		self.geom.setPosition(pos)
		self.geom.setQuaternion(quat)
		
		if self.visualization:
			self.visualization.setQuat(quat)
			self.visualization.setPos(pos)
		
		self.prevPos = pos

"""
Simpler dynamic object, which has no continuous collision detection.

This type of object can be used for large and slow moving objects, but
shouldn't be used for small or fast moving ones.

This dynamic object has no protection against the tunneling effect.
"""
class dynamicObjectNoCCD(staticObject):
	def __init__(self, map):
		staticObject.__init__(self, map)
		self.objectType = "dynamic"
	
	def getLinearVel(self):
		return self.body.getLinearVel()
	
	"""
	Setting a standard body with Box mass.
	It uses setBoxTotal instead of setBox, so give weight and not
	density.
	"""
	def setBoxBody(self, weight, size):
		if not self.geom:
			print "you must set geom before setting body"
			return False
		if not self.nodePath:
			print "you must set nodepath before setting body"
			return False
		
		"""
		IMPORTANT
		
		To prevent getting nan values when a box Body is rotating, set
		it to a cube. This still allows the Geom to collide correctly,
		but prevents the body from gaining speed by itself when rotating.
		"""
		maxSize = self.geomSize[0]
		for s in self.geomSize:
			if s > maxSize:
				maxSize = s
		bodySize = Vec3(maxSize, maxSize, maxSize)
		
		self.mass = OdeMass()
		self.mass.setBoxTotal(weight, bodySize)
		
		self.body = OdeBody(self.map.worldManager.world)
		self.body.setMass(self.mass)
		self.body.setPosition(self.nodePath.getPos(render))
		self.body.setQuaternion(self.nodePath.getQuat(render))
		
		self.geom.setBody(self.body)
	
	"""
	Setting a standard body with Sphere mass.
	It uses setSphereTotal instead of setSphere, so give weight and not
	density.
	"""
	def setSphereBody(self, weight, radius):
		if not self.geom:
			print "you must set geom before setting body"
			return False
		if not self.nodePath:
			print "you must set nodepath before setting body"
			return False
			
		self.mass = OdeMass()
		self.mass.setSphereTotal(weight, radius)
		
		self.body = OdeBody(self.map.worldManager.world)
		self.body.setMass(self.mass)
		self.body.setPosition(self.nodePath.getPos(render))
		self.body.setQuaternion(self.nodePath.getQuat(render))
		
		self.geom.setBody(self.body)
		
	def getBody(self):
		return self.body
		
	def setPos(self, pos=None):
		staticObject.setPos(self, pos)
		if pos is None:
			self.body.setPosition(self.nodePath.getPos(render))
		else:
			self.body.setPosition(pos)
	
	"""
	Update the node's position accordingly to the geom's position.
	"""
	def update(self, stepSize):
		pos = Vec3(self.geom.getPosition())
		quat = Quat(self.geom.getQuaternion())
		
		self.nodePath.setPosQuat(render, pos, quat)
		self.previousPos = pos
		
	def destroy(self):
		staticObject.destroy(self)
		self.body.destroy()
		del self.body
		del self.mass

"""
The more complex version of a dynamic object, featuring
Continuous Collision Detection.

This version is not a subject to tunneling, so it should be used for fast
moving and/or small objects.

The previous version of this class suffered from incorrect bouncing. In order to prevent
the bodies from sticking permanently to the surfaces they collided with I used to cut down
their velocity to prevent the CCD from kicking in when it was not supposed to.

This caused the objects to loose a lot of their energy on collisions, resulting in
unrealistic behavior.

This version, however, doesn't have this problem any more. I've changed the implementation
to put holes into the CCD (if that lights a warning light in your head that's good, it should)
so it never kicks in right after a collision. This approach theoretically, raises
the probability of tunneling in certain situations (e.g. when an object is very small and
collides with a bumpy surface or when an object is thrown into a corner of a room).
However, while the CCD is no longer 100% accurate, I would say with correct setup
it's close to 95 or 97 % which is a good price for correct bouncing, I think.

If you do find your objects tunneling there are a couple of variables that will help
you tune the new CCD mechanics and eliminate the problem.

Those variables are:
	- self.ccdCollisionSpace
	- self.ccdDistMultiplier
	- self.ccdSlidingAngle

They are explained in detail below.

The other remaining limitation is that it supports only box and sphere, and no compound shapes.
This should be enough for most games and most cases when CCD is needed, though.

Also, be aware that this class is much slower than the version without CCD!
"""
class dynamicObjectCCD(dynamicObjectNoCCD):
	def __init__(self, map):
		dynamicObjectNoCCD.__init__(self, map)
		
		"""
		This object is handled by the World Manager in the exact same way as a normal Dynamic Object.
		"""
		self.objectType = "dynamic"
		
		"""
		The CCD process can be visualized.
		"""
		self.showCCD = False
		
		"""
		Two crucial variables.
		
		previousPos of the geom allows the system to know where
		to put the CCD helper geoms.
		
		ccdCollidingGeomPos is set to the colliding helper geom
		which is nearest the previous position of the real geom.
		"""
		self.previousPos = None
		self.ccdCollidingGeomPos = None
		
		"""
		ccDist is the distance between the helper geoms. It's set to it's
		actual value later, automatically.
		"""
		self.ccdDist = 0.0
		
		"""
		With this variable you can control the precision of the CCD process.
		
		3.0 is the most sensible value, but the higher you set it, the less
		the objects will 'sink' into environment before bumping off of it.
		
		The higher this value is, the more expensive the CCD process it.
		"""
		self.ccdDistMultiplier = 3.0
		
		"""
		NEW IN VERSION 1.2.0
		
		Those three variables are introduced because of the aforementioned changes in the
		CCD process meant to prevent the extensive damping effect.
		
		The first one (nextFrame) is set to true whenever a collision is detected, so that
		the CCD knows it should now perform the "Permanent-Sticking Prevention".
		
		The other two are meant for tunning that Permanent-Sticking Prevention.
		
		The second variable (ccdCollisionSpace) tells the CCD how big you want the gap between
		the collision place and the new set of helper geoms to be. The default value is 4
		which means that after a collision the new CCD process will be initiated NOT in
		the place of the collision, but 4 * ccdDist from the collision point, in order to
		leave enough space for the body to bounce correctly.
		
		You can (and probably should) tune that value taking into consideration the size of
		the object (and the resulting ccdDist, which is always the geom's smallest dimension),
		the surfaces' bumpyness, the timestep and the scenarios in which the object is
		expected to collide. I found 4 to be the best value in all cases I examined.
		
		Note that if you set the ccdCollisionSpace to a very high value it will result in the
		geom tunneling when thrown into a corner because there will be a huge gap in which the
		other wall might just fall into.
		
		The third variable contains a list of two values (min and max) in degrees.
		Using these values you can tune the CCD to treat a collision under a certain angle (between min and max)
		as sliding. When a collision is considered sliding by the CCD it will not kick in AT ALL because it knows,
		that the object will move (almost) parallel to the surface it's on, so any collision will better
		be detected by the geom itself, with no help from the helper geoms needed.
		
		Obviously, this also has a downside since when an object is small, travels at very, very high speed
		and has a liberal ccdSlidingAngle it might tunnel. Still, that's why this value is not hardcodded.
		If you want to, you can set it to [0.0, 0.0] and the CCD will never act sliding.
		
		I introduced that because the CCD always moves the geom to the first collision place detected
		by the first of the helper geoms which resulted in any sliding movement becoming jerky and slow.
		
		Those three variables allow the CCD to finally work as it should while still retaining almost 100%
		tunneling prevention.
		"""
		self.nextFrame = False
		self.ccdCollisionSpace = 4
		self.ccdSlidingAngle = [80.0, 100.0]
		
		"""
		The list that holds the helper objects.
		"""
		self.helperObjects = []
	
	"""
	Reimplementation of the dynamicObjectNoCCD.setBoxGeom method
	"""
	def setBoxGeom(self, size):
		dynamicObjectNoCCD.setBoxGeom(self, size)
		
		"""
		Automatically find the CCD Distance by searching for the
		shortest edge of the box.
		"""
		self.ccdDist = self.geom.getLengths()[0]
		for len in self.geom.getLengths():
			if len < self.ccdDist:
				self.ccdDist = len
		return True
	
	"""
	Reimplementation of the dynamicObjectNoCCD.setSphereGeom method
	"""
	def setSphereGeom(self, radius):
		dynamicObjectNoCCD.setSphereGeom(self, radius)
		
		"""
		Set the CCD Distance to the sphere's radius.
		I multiply it by 1.7 for better results -- just out of observation.
		"""
		self.ccdDist = radius * 1.7
		
	def setBoxBody(self, weight, size):
		dynamicObjectNoCCD.setBoxBody(self, weight, size)
		self.previousPos = self.nodePath.getPos(render)
		
	def setSphereBody(self, weight, radius):
		dynamicObjectNoCCD.setSphereBody(self, weight, radius)
		self.previousPos = self.nodePath.getPos(render)
	
	"""
	What the exception says
	"""
	def setTrimeshGeom(self, model):
		raise Exception("Trimesh is not supported for ccd!!")
		return False
	
	"""
	The callback method for Helper Geom objects.
	
	This allows me to find the nearest collision happening between
	two frames.
	"""
	def castCollision(self, entry, object1, object2):
		"""
		Don't care about collisions between this object and helper objects,
		or between two helper objects
		"""
		if object2 is self or object2.objectType == "ccd":
			return
		
		"""
		For convenience
		"""
		geom = object1.geom
		
		"""
		New in 1.2.0
		Make sure the object slides correctly. When the CCD visualization is enabled it
		leaves a black debug wiregeom where the CCD is omited...
		"""
		normal = entry.getContactGeom(0).getNormal()
		linVel = self.body.getLinearVel()
		linVel.normalize()
		
		"""
		...As you can see the angle is calculated between the normal and the object's linear velocity...
		"""
		angle = abs(Vec3(normal).signedAngleDeg(Vec3(linVel), Vec3(normal)))
		
		"""
		...and when the angle's absolute value is between the min and max of the ccdSlidingAngle variable
		the CCD is omited. NOTE that ALL OF IT. Unlike the ccdCollisionSpace mechanism this one doesn't do
		CCD at all, because otherwise, if there was even one helper geom included, the object would not reach
		this frame's destination, but instead it would've stopped on the helper. So in this case the helper geoms
		would actually be "obstructing geoms".
		"""
		if angle > self.ccdSlidingAngle[0] and angle < self.ccdSlidingAngle[1]:
			print "ANGLE", angle, self.ccdSlidingAngle[0], self.ccdSlidingAngle[1]
			if self.showCCD:
				self.placeDebug(geom.getPosition(), Vec4(0, 0, 0, 1))
			return
		
		"""
		If there was no previous collision, default to this one and return.
		"""
		if self.ccdCollidingGeomPos is None:
			self.ccdCollidingGeomPos = geom.getPosition()
			return
		
		"""
		Get the distance between this helper collision and the previous
		position of this object.
		"""
		vNew = self.previousPos - geom.getPosition()
		dNew = vNew.length()
		
		"""
		Get the distance between the previous nearest helper collision
		and the previous position of this object.
		"""
		vOld = self.previousPos - self.ccdCollidingGeomPos
		dOld = vOld.length()
		
		"""
		If the new collision is nearer to the previous position than the
		previous nearest collision, switch them.
		
		This is used to make sure we don't get the collision from the other
		side of a wall, for example.
		"""
		if dNew > dOld:
			self.ccdCollidingGeomPos = geom.getPosition()
	
	"""
	New in 1.2.0
	
	This method is used to create the helper geoms within the update method.
	It was previously embedded in the update method.
	"""
	def createHelpers(self, pos, dist):
		"""
		Only do CCD if the object travaled more distance in this frame,
		than the value of the ccdDist variable.
		"""
		if dist > (self.ccdDist / self.ccdDistMultiplier):
			"""
			How many helper geoms are needed?
			"""
			amount = dist / self.ccdDist * self.ccdDistMultiplier
			
			"""
			The distance (vector) between the helper geoms
			"""
			vec = pos - self.previousPos
			vecPart = vec / amount
			
			amount = int(amount)
			
			"""
			If it's the next frame after a collision was detected, then start putting
			the CCD helpers ccdCollisionSpace-away from the previousPos.
			
			If not, start with the previousPos.
			"""
			if self.nextFrame:
				r = range(self.ccdCollisionSpace, amount)
			else:
				r = range(amount)
			
			"""
			Start placing the helpers.
			"""
			for i in r:
				"""
				The position vector of the new helper geom.
				"""
				castPos = self.previousPos + (vecPart * float(i))
				self.createSingleHelper(castPos)
	
	"""
	New in 1.2.0
	
	This method is used to create a single helper geom within the createHelpers method.
	It was previously embedded in the update method.
	
	This is just for easier code management.
	"""
	def createSingleHelper(self, castPos, debugColor = Vec4(0.8, 0.8, 0.8, 1)):
		"""
		Create the helper object.
		"""		
		obj = staticObject(self.map)
		
		"""
		A special object type for ccd helper geoms, which gives them
		privileges in World Manager collision handling.
		"""
		obj.objectType = "ccd"
		
		"""
		Set the collision callback to point to this dynamicObjects's
		castCollision method. That way we can get the collisions from
		the helper object.
		"""
		obj.collisionCallback = self.castCollision
		
		"""
		Set the geoms and place the debug wiregeoms.
		"""
		if str(self.geom.getClassType()) == "OdeBoxGeom":
			obj.setBoxGeom(self.geom.getLengths())
		
		elif str(self.geom.getClassType()) == "OdeSphereGeom":
			obj.setSphereGeom(self.geom.getRadius())
		
		if self.showCCD:
			self.placeDebug(castPos, debugColor)
		
		"""
		Set the cat/col bit masks to the same value as this object's
		"""
		obj.setCatColBits(self.bitsName)
		
		"""
		Set the helper's position, quaternion, append it to the
		geomCast list and add it, along with it's data,
		to the World Manager.
		"""
		obj.setPos(castPos)
		obj.setQuat(self.geom.getQuaternion())
		
		self.helperObjects.append(obj)
		self.map.worldManager.addObject(obj)
	
	"""
	Completely different update callback then the one from dynamicObjectNoCCD
	"""
	def update(self, stepSize):
		quat = Quat(self.geom.getQuaternion())
		
		"""
		Getn the distance the object traveled in this frame.
		"""
		vel = self.body.getLinearVel()
		speed = vel.length()
		dist = speed * stepSize
		
		"""
		Destroy all Helper Geoms and empty the geomCast list.
		"""
		for obj in self.helperObjects:
			self.map.worldManager.removeObject(obj)
			obj.collisionCallback = None
			obj.destroy()
		self.helperObjects = []
		
		if self.ccdCollidingGeomPos:
			"""
			There was a collision detected by one of the helper geoms, stop
			the CCD process.
			"""
			
			"""
			For convenience.
			"""
			pos = self.ccdCollidingGeomPos
			
			"""
			Red debug wiregeom, meant to show the place where the CCD detected
			the collision.
			"""
			if self.showCCD:
				self.placeDebug(pos, Vec4(1, 0, 0, 1))
			
			"""
			Set the position of the geom AND THE BODY to the one detected
			by helper geoms.
			"""
			self.geom.setPosition(pos)
			self.body.setPosition(pos)
			
			"""
			Previously in here the object's velocity was cut down to prevent
			the CCD from making the object stick permanently to a surface.
			Now the nextFrame variable is used instead, to inform the CCD that
			there was a collision in this frame so it knows how to create
			the helpers for the next frame.
			"""
			self.nextFrame = True
			
		else:
			"""
			The helper geoms detected no collision, start/continue the CCD process.
			"""
			
			"""
			A debug geom meant to show the current position of the body. Useful
			for tweaking the CCD variables as it shows how much the object moved
			in one frame and how that relates to collisions detected and so on.
			"""
			#if self.showCCD:
			#	self.placeDebug(self.body.getPosition(), Vec4(0, 1, 1, 1))
			
			pos = Vec3(self.geom.getPosition())
			
			"""
			Self explanatory, I guess. Before the whole process was done here, but
			I moved it out for convenience.
			"""
			self.createHelpers(pos, dist)
			
			"""
			This MUST be here or the CCD won't work at all as it would think
			it's 1 frame after a collision all the time.
			"""
			self.nextFrame = False
		
		"""
		Update the geom's position, clear the colliding (helper) geom position
		variable and set previous position to current position for the next frame.
		"""
		self.nodePath.setPosQuat(render, pos, quat)
		self.ccdCollidingGeomPos = None
		self.previousPos = pos
		
		if self.visualization:
			self.visualization.setQuat(quat)
			self.visualization.setPos(pos)
	
	"""
	Place the debug wiregeoms using the fantastic FenrirWolf's code.
	"""
	def placeDebug(self, pos, color):
		if str(self.geom.getClassType()) == "OdeBoxGeom":
			np = wireGeom().generate("box", extents = list(self.geom.getLengths() * 0.5))
		elif str(self.geom.getClassType()) == "OdeSphereGeom":
			np = wireGeom().generate("sphere", radius = self.geom.getRadius())
		
		np.reparentTo(render)
		
		np.setPos(render, pos)
		np.setQuat(render, self.geom.getQuaternion())
		
		np.setColor(color)
	
	def destroy(self):
		"""
		Make sure we remove the helper objects.
		"""
		for obj in self.helperObjects:
			self.map.worldManager.removeObject(obj)
			if self.showCCD:
				obj.nodePath = None
			obj.destroy()
		self.helperObjects = []
		
		dynamicObjectNoCCD.destroy(self)
		
		del self.helperObjects

"""
That's just for convenience, setting the default dynamicObject.
"""
global dynamicObject
dynamicObject = dynamicObjectCCD
#dynamicObject = dynamicObjectNoCCD

class rayObject(physicalObject):
	def __init__(self, map):
		physicalObject.__init__(self, map)
		self.objectType = "ray"
		
	def setRayGeom(self, length, rayAttribs = None):
		self.geom = OdeRayGeom(self.map.worldManager.getSpace(), length)
		if rayAttribs is not None:
			self.geom.set(*rayAttribs)
			
		self.synchPosQuatToNode()

"""
Explosion class for ODE

You use it by just creating it with the required attributes, it will 
self-destruct as soon as it runs out of power.
"""
class explosion(kinematicObject):
	def __init__(self, map, pos, force = 100.0, radius = 0.5):
		"""
		You might notice that I'm not setting a collision callback here,
		like I would with OdeGeomData previously. That's because the
		self.collisionCallback method is used (same with all other objects).
		"""
		
		kinematicObject.__init__(self, map)
		
		"""
		Note that previously (with OdeGeomData) this was done with isTrigger
		variable. Now it's just a separate object type.
		"""
		self.objectType = "trigger"
		
		self.timeElapsed = 0.0
		self.speed = 2000.0
		self.force = force
		self.currentForce = 0.0
		self.radius = radius
		
		self.collisions = []
		
		self.setSphereGeom(radius)
		self.setPos(pos)
		
		self.map.worldManager.addObject(self)
		
	"""
	Get all geoms within the range
	
	You might notice this method is FAR simpler and shorter than previously.
	You'll find out why in the World Manager class.
	"""
	def collisionCallback(self, entry, object1, object2):
		self.collisions.append([object2, entry.getContactGeom(0).getNormal(), entry.getContactPoint(0)])
		
	def update(self, timeStep):
		self.timeElapsed += timeStep
		
		if self.timeElapsed > .1:
			self.map.worldManager.removeObject(self)
			self.destroy()
			return
		
		force = self.force - self.geom.getRadius()/10.0
		
		for obj, normal, point in self.collisions:
			if obj.body:
				forceVector = -normal * force
				obj.body.enable()
				obj.body.addForce(forceVector)
				
		self.radius += self.speed * self.timeElapsed**2
		self.geom.setRadius(self.radius)
		
		self.collisions = []

"""
Most important class which... well, manages the world.
"""
class odeWorldManager(object):
	def __init__(self):
		self.world = OdeWorld()
		self.world.setGravity(0, 0, -9.81)
		
		"""
		An important optimization. Manipulate the values to get the correct behaviour,
		but I advice not to turn it off.
		
		What it does, is it puts to sleep (disables) objects that are not used (the combined
		forces set on them are lower than thresholds set) for a specific time/number of steps.
		"""
		self.world.setAutoDisableFlag(1)
		self.world.setAutoDisableAngularThreshold(0.3)
		self.world.setAutoDisableLinearThreshold(0.1)
		self.world.setAutoDisableSteps(30)
		self.world.setAutoDisableTime(0.0)
		
		"""
		Standard ODE stuff
		"""
		self.contactGroup = OdeJointGroup()
		self.space = OdeSimpleSpace()
		
		"""
		it's set later, here it's just initialized.
		"""
		self.stepSize = None
		
		"""
		The list of objects in the simulation.
		
		If you used the previous version, you might remember there were two lists before,
		one for dynamics, one for kinematics. This is no longer needed because of the
		*Object classes above.
		"""
		self.objects = []
		
		"""
		This is used to get objects by it's geom surface type. It's needed because
		of ditching the odeGeomData. Basically this move made all object code MUCH
		more readable and simple, but it came with the price of this nasty piece.
		
		I might eventually find a better way to handle this, or not, but in any case
		possible changes to this area will not affect your code.
		
		More on that in the addObject, removeObject and update methods.
		"""
		self.lastGeomIndex = 0
		self.objectGeomIndexes = {}
		
		"""
		Convenient way to pause the world.
		"""
		base.accept("pause", self.pause)
		base.accept("unpause", self.unpause)
	
	def pause(self):
		self.stopSimulation()
		
	def unpause(self):
		self.startSimulation(self.stepSize)
	
	"""
	This function gets the size of a Node's bounding box. It's used to create OdeBoxGeoms
	from Nodes in physicalObject.setBoxGeomFromNodePath method.
	
	FOR BEST RESULTS (in Blender) make sure your models are only rotated in object-mode, while
	remaining aligned with their local XYZ in edit-mode. Also, make sure the objects have only
	as much rotation as they *really* need. Otherwise you might get artifacts with this method.
	"""
	def extractSizeForBoxGeom(self, node):
		quat = node.getQuat(render)
		node.setHpr(render, Vec3(0, 0, 0))
		
		p1, p2 = node.getTightBounds()
		
		sx = abs(p1.getX() - p2.getX())
		sy = abs(p1.getY() - p2.getY())
		sz = abs(p1.getZ() - p2.getZ())
		
		node.setQuat(render, quat)
		
		return Vec3(sx, sy, sz)
	
	def getSpace(self):
		return self.space
		
	def destroy(self):
		self.stopSimulation()
		for object in self.objects:
			self.removeObject(object)
		
		self.contactGroup.empty()
		self.space.destroy()
		self.contactGroup.destroy()
		self.world.destroy()
		
		del self.space
		del self.contactGroup
		del self.world
		
		del self.objects
		
		return True
	
	"""
	Collide only one object against the rest of the space. I use it to check
	whether an object can be dropped somewhere.
	
	I'm worried that this method might eventually proove too inefficient for
	really large worlds, so be aware it might get deprecated in the future.
	Still, there's a lot of potential for optimization here, me thinks, so time will tell.
	
	CONSIDER THIS METHOD DEPRECATED. There is no replacement for it because it generally
	should not be needed, actually.
	"""
	def collideSelected(self, selected, exclude=[]):
		entries = []
		
		selCat = selected.getCategoryBits()
		selCol = selected.getCollideBits()
		
		for idx in range(self.space.getNumGeoms()):
			geom = self.space.getGeom(idx)
			
			# Check bitmasks
			geomCat = geom.getCategoryBits()
			geomCol = geom.getCollideBits()
			if (selCat & geomCol) | (geomCat & selCol) == BitMask32(0):
				continue
			
			if not geom.isEnabled():
				continue
			if geom in exclude:
				continue
			if self.getObjectByGeomSurfaceIndex(geom).objectType in ["trigger", "ccd", "ray"]:
				continue
			
			entry = OdeUtil.collide(selected, geom, 1)
			if entry.getNumContacts():
				entries.append(entry)
		return entries
	
	"""
	Do a raycast against the space using an existing ray.
	"""
	def doRaycast(self, ray, exclude=[]):
		ray.enable()
		
		closestEntry = None
		closestGeom = None
		
		rayCat = ray.getCategoryBits()
		rayCol = ray.getCollideBits()
		
		for idx in range(self.space.getNumGeoms()):
			geom = self.space.getGeom(idx)
			if not geom.isEnabled():
				continue
			if geom in exclude:
				continue
			geomCat = geom.getCategoryBits()
			geomCol = geom.getCollideBits()
			calc = (rayCat & geomCol) | (geomCat & rayCol)
			if calc == BitMask32(0):
				continue
			entry = OdeUtil.collide(ray, geom, 2)
			if entry.getNumContacts():
				depth = entry.getContactGeom(0).getDepth()
				if closestEntry is None:
					closestEntry = entry
					closestGeom = geom
				elif depth < closestEntry.getContactGeom(0).getDepth():
					closestEntry = entry
					closestGeom = geom
		
		ray.disable()
		
		if closestGeom:
			closestobject = self.getObjectByGeomSurfaceIndex(closestGeom)
		else:
			closestobject = None
		
		return (closestEntry, closestobject)
	
	"""
	Create a ray and do a raycast against the space with it.
	"""	
	def doRaycastNew(self, bitMaskName, length, rayAttribs, exclude=[]):
		print "RAYCASTING new"
		
		ray = OdeRayGeom(self.space, length)
		ray.set(*rayAttribs)
		ray.setCollideBits(bitMaskDict[bitMaskName][0])
		ray.setCategoryBits(bitMaskDict[bitMaskName][1])
		
		closestEntry, closestObject = self.doRaycast(ray, exclude)
		
		ray.destroy()
		del ray
		
		return (closestEntry, closestObject)
	
	"""
	Long live long and descriptive method names. Ok, to the point.
	
	This is the main replacement for the odeGeomData stuff here.
	It uses the objectGeomIndexex dictionary, which contains the
	surfaceType value assigned to the geom (key) and the object
	that uses this geom (value).
	
	It's used to get from the geom to the object. The other way is simple,
	but this is tricky, since OdeGeoms in Panda don't support any kind of
	taging. If they did, it would be super easy, and wouldn't require such
	nasty hacks.
	"""
	def getObjectByGeomSurfaceIndex(self, geom):
		idx = self.space.getSurfaceType(geom)
		return self.objectGeomIndexes[idx]
	
	"""
	A more flexible replacement for AutoCollide. In this version getting a major overhaul and optimization (yay).
	
	If you've used 0.9 (and earlier) you will notice, that this time I work on OBJECTS rather than GEOMS. This
	is an important simplification and it allows for some optimization too. That's why I ditched the OdeGeomData
	class, because without it everything is a lot more straightforward, and it prooved to be pointless, since
	with the CopperODE design it could not be used by more than one object at the same time anyway.
	
	Additionally, notice that the collision callbacks are now called with the object1 and object2 values, where
	object1 is the one the callback method belongs to, while object2 is the other object taking part in the collision.
	You might want to ask why I even send object1 then, since it's the same as "self" in the callback method anyway.
	Well, exactly for that reason. It doesn't hurt performance (just one argument more or less), but made debugging
	a lot easier initially, so I decided to keep it, just in case.
	
	Anyway, I hope you'll notice how much cleaner the method is now.
	"""
	def handleCollisions(self, arg, geom1, geom2):
		entry = OdeUtil.collide(geom1, geom2)
		
		if entry.isEmpty():
			return
		
		"""
		Get the physical objects that use those geoms using their surface type.
		I gotta make a request for pythonTags on odeGeoms... seriously.
		
		On a side note, initially I used a for loop for that. Heck, that was slow beyond any description.
		"""
		object1 = self.getObjectByGeomSurfaceIndex(geom1)
		object2 = self.getObjectByGeomSurfaceIndex(geom2)
		
		"""
		No collisions between "naked" geoms are permited. Physical objects have a monopoly on collisions here.
		"""
		if object1 is None or object2 is None:
			return
		
		"""
		Get the types of the two objects for convenience and better readability.
		"""
		type1 = object1.objectType
		type2 = object2.objectType
		
		"""
		Ignore collisions when both objects are tiggers or static objects.
		"""
		ignoredTypes = ["trigger", "static"]
		if type1 in ignoredTypes and type2 in ignoredTypes:
			return
		
		"""
		Ignore collisions between rays, ccd helpers and/or triggers.
		Note that we've already sorted out collisions between triggers and statics,
		but now we DO want statics here, because rays and ccd helpers must collide
		with those.
		
		This and the previous instructions are very important optimizations.
		Obviously, feel free to tweak this as needed, just make sure not to
		handle collisions between two static objects -- doing those will
		eat your FPS badly.
		"""
		ignoredTypes = ["ray", "ccd", "trigger"]
		if type1 in ignoredTypes and type2 in ignoredTypes:
			return
		
		"""
		Get the bodies of the two objects for convenience and better readability.
		"""
		body1 = object1.body
		body2 = object2.body
		
		"""
		And now we add statics to ignored types to get the total of:
		["ray", "ccd", "trigger", "static"].
		
		This is because the next step is actually creating collisions between
		objects (so that ODE can deal with physical interaction).
		Yet for the objects of the aforementioned types we just want the
		collision callbacks called.
		"""
		ignoredTypes += ["static"]
		
		"""
		Create collision joints between certain objects.
		"""
		if body1 or body2 and type1 not in ignoredTypes and type2 not in ignoredTypes:
			"""
			Don't do collisions between two disabled dynamic objects.
			"""
			if body1 and body2 and not body1.isEnabled() and not body2.isEnabled():
				return
			if body1 and not body1.isEnabled() and type2 == "static":
				return
			if body2 and not body2.isEnabled() and type1 == "static":
				return
			
			"""
			Make sure a collision between a kinematic object and a dynamic one
			wakes up the later.
			"""
			if body1 and type2 == "kinematic":
				body1.enable()
			if body2 and type1 == "kinematic":
				body2.enable()
			
			"""
			The standard ODE contact joint setting voodoo starts here.
			"""
			surfaceParams = OdeSurfaceParameters()
			
			"""
			Be carefull with those flags. softERP and softCFM for example don't like
			it when approx is enabled. If you want to make water, for example, you gonna
			need to "if" here and disable approx for that.
			
			Since version 1.2.0 additionally enabled are:
				- bounce
				- motion1
				- motion2
			"""
			# Enable a more accurate friction model (approx)
			# Flags: mu2, fdir1, bounce, softERP, softCFM, motion1, motion2, slip1, slip2, approx1, approx2, approx
			surfaceParams.setMode(0b111000110111)
			
			surfaceParams.setMu(object1.surfaceFriction)
			surfaceParams.setMu2(object2.surfaceFriction)
			surfaceParams.setSlip1(object1.surfaceSlip)
			surfaceParams.setSlip2(object2.surfaceSlip)
			
			"""
			Honestly, I'm not sure I'm doing that the correct way, but simply found it to be the best
			way I've tried so feel free to experiment with the bounce values and their handling ;).
			"""
			bounce = object1.surfaceBounce * object2.surfaceBounce
			if bounce > 1.0:
				bounce = 1.0
			
			surfaceParams.setBounce(bounce)
			surfaceParams.setBounceVel(object1.surfaceBounceVel * object2.surfaceBounceVel)
			
			numContacts = entry.getNumContacts()
			
			for i in range(numContacts):
				cgeom = entry.getContactGeom(i)
				
				contactPoint = entry.getContactPoint(i)
				
				contact = OdeContact()
				contact.setGeom(cgeom)
				
				"""
				Pass the bodies and other stuff to the appropriate methods to handle
				the friction.
				
				Before you ask, ODE doesn't support rolling friction, so
				any balls you might have in your game will spin infinitely.
				To prevent that, you might try adding damping forces.
				"""
				if body1:
					self.handleCollisionsFriction(body1, object2, contact, surfaceParams)
				elif body2:
					self.handleCollisionsFriction(body2, object1, contact, surfaceParams)
				
				contact.setSurface(surfaceParams)
				
				contactJoint = OdeContactJoint(self.world, self.contactGroup, contact)
				contactJoint.attach(body1, body2)
		
		"""
		Call the collision callbacks on both objects. Note the positions of object1 and object2
		in both callbacks. They depend on which object we call the collision callback on.
		
		I did this to make sure I don't have to check that inside the callbacks themselves.
		"""
		object1.collisionCallback(entry, object1, object2)
		object2.collisionCallback(entry, object2, object1)
	
	def handleCollisionsFriction(self, body, object, contact, surfaceParams):
		"""
		This (in conjuction with the motion1 and *2 flags) allows the dynamic objects
		to be "carried" by moving platforms.
		"""
		if object.objectType == "kinematic":
			"""
			Get the object's linear velocity.
			"""
			objLinVel = object.getLinearVel()
			
			"""
			Tell ode that the collision surface moves. Yes, the linear velocity must be squared.
			"""
			surfaceParams.setMotion1(objLinVel.lengthSquared())
			
			"""
			Set the friction direction one to the linear velocity of the kinematic object.
			The friction direction two is calculated automatically by ODE.
			"""
			contact.setFdir1(objLinVel)
		
		else:
			"""
			Set the friction direction one to the linear velocity of a body.
			The friction direction two is calculated automatically by ODE.
			"""
			contact.setFdir1(body.getLinearVel())
	
	"""
	Add object (*Object class' instance) to the simulation
	
	At the same time I assign an index to that Geom/Object pair
	and put it into that objectGeomIndexes dictionary.
	
	Have I mentioned the need for odeGeom python tagging?
	"""
	def addObject(self, obj):
		geom = obj.getGeom()
		
		self.lastGeomIndex += 1
		self.space.setSurfaceType(geom, self.lastGeomIndex)
		
		self.objectGeomIndexes[self.lastGeomIndex] = obj
		
		self.objects.append(obj)
	
	"""
	Remove object from simulation
	"""
	def removeObject(self, object):
		if object not in self.objects:
			return False
		
		geomIndex = self.space.getSurfaceType(object.geom)
		del self.objectGeomIndexes[geomIndex]
		
		idx = self.objects.index(object)
		self.objects.pop(idx)
		
		return True
	
	"""
	Step the simulation
	"""
	def simulationTask(self, task):
		self.space.collide("", self.handleCollisions)
		self.world.quickStep(self.stepSize)
		self.contactGroup.empty()
		
		"""
		Update the objects in the simulation
		"""
		for object in self.objects:
			object.update(self.stepSize)
				
		return task.again
	
	def startSimulation(self, stepSize):
		self.stepSize = stepSize
		taskMgr.doMethodLater(stepSize, self.simulationTask, "ODE_simulationTask")
		
	def stopSimulation(self):
		taskMgr.remove("ODE_simulationTask")
