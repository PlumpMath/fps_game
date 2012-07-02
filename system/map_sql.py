from direct.actor import Actor
from pandac.PandaModules import *

from system.odeWorldManager import *
from system.trigger import *
from character import *
from inventory import *

from assets.door import *
from assets.chair import *
from assets.movingPlatform import *
from weapons.grenade import *
from weapons.guns import *

class map_sql(object):
    def __init__(self):
        self.defaultShowCCD = False
        
        self.mapObjects = {
                           "static" : [],
                           "triggers" : [],
                           "characters" : [],
                           "dynamics" : [],
                           "kinematics" : [],
                           }
        
        #self.mapFile = "./models/terrain/grass2"
        #self.terrainFile = "./models/terrain/snowy"
        self.terrainFile = "./models/terrain/hmt4"
        #self.terrainFile = "./models/terrain/ground2-1"
        self.playerSpawnPointFile = "./graphics/models/box"
        self.alightSpawnPointFile = "./graphics/models/box"
        self.chairSpawnPointFile = "./graphics/models/chair"
        
        self.worldManager = odeWorldManager()
        
        self.simTimeStep = 1.0/60.0
        
    def create(self):
        self.terrain = loader.loadModel(self.terrainFile)
        self.terrain.setPos(0, 0, .01)
        self.terrain.setScale(100, 100, 100)
        self.terrain.flattenLight()
        self.terrain.reparentTo(render)
        
        #self.terrain = GeoMipTerrain("terrain")
        #self.terrain.setHeightfield("./models/heigthmaps/heightmap1.png")
        #self.terrain.getRoot().reparentTo(render)
        #self.terrain.generate()
        
        self.solidTriMeshGeom(self.terrain)
        #self.solidBoxGeom(self.terrain)
        
        self.playerSpawnPoint = loader.loadModel(self.playerSpawnPointFile)
        self.playerSpawnPoint.setPos(0, 0, 20)
        
        self.alightSpawnPoint = loader.loadModel(self.alightSpawnPointFile)
        self.alightSpawnPoint.setPos(0, 0, 50)
        self.alight = self.alight(self.alightSpawnPoint)
        
        self.chairSpawnPoint = loader.loadModel(self.chairSpawnPointFile)
        self.chairSpawnPoint.setPos(0, 0, 2)
        self.chairSpawnPoint.reparentTo(render)
        self.c = self.chair(self.chairSpawnPoint)
        
        self.worldManager.startSimulation(self.simTimeStep)
        
        
        self.player = self.playerPosition(self.playerSpawnPoint)
        
        self.player.enableInput()
        self.player.enableMovement()
        
    def destroy(self):
        print "DESTROYING MAP"
        
        render.clearLight()
        self.worldManager.stopSimulation()
        
        print "map_sql -> destroy -> map objects:\n" + "="*60
        print self.mapObjects, "\n"+"="*60
        
        for catName, category in self.mapObjects.iteritems():
            for obj in list(category):
                print "map -> destroy -> removing", obj, obj.objectType
                obj.destroy()
                
        print "map_sql -> destroy -> finished removing objects"
        self.mapObjects = {}
        
        print "map_sql -> destroy -> removing player"
        #self.player.destroy()
        print "map_sql -> destroy -> destroy world manager"
        self.worldManager.destroy()
        print "map_sql -> destroy -> world manager destroyed, unload map model"
        #loader.unloadModel(self.terrain)
        self.terrain.removeNode()
        
        del self.mapObjects
        del self.worldManager
        del self.player
        del self.terrain
        
    def removeObject(self, object):
        for category in self.mapObjects.keys():
            if object in self.mapObjects[category]:
                self.removeObjectByCategory(object, category)
                
    def removeObjectByCategory(self, object, category):
        self.worldManager.removeObject(object)
        try:
            idx = self.mapObjects[category].index(object)
            self.mapObjects[category].pop(idx)
            
            return True
        except:
            return False
        
                                                           
        
    def solidBoxGeom(self, node):
        pos = node.getPos(render)
        quat = node.getQuat(render)
        
        object = staticObject(self)
        
        object.setBoxGeomFromNodePath(node)
        
        object.setPos(pos)
        object.setQuat(quat)
        
        object.setCatColBits("environment")
        
        self.worldManager.addObject(object)
        
        self.mapObjects["static"].append(object)
        
    def solidTriMeshGeom(self, node):
        static = staticObject(self)
        static.setNodePath(node)
        
        static.setTrimeshGeom(node)
        
        static.setCatColBits("environment")
        
        self.worldManager.addObject(static)
        
        self.mapObjects["static"].append(static)
        
        return static
    
    def alight(self, node):
        alight = AmbientLight("ambientLight")
        alight.setColor(Vec4(.7, .7, .7, 1.0))
        alightNP = render.attachNewNode(alight)
        render.setLight(alightNP)
        
        #alight.setShadowCaster(True, 512, 512)
        
        return alightNP
        
    def dlight(self, node):
        dlight = DirectionalLight("directionalLight")
        dlight.setDirection(Vec3(node.getHpr()))
        dlight.setColor(Vec4(0.3, 0.3, 0.3, 1))
        dlightNP = render.attachNewNode(dlight)
        render.setLight(dlightNP)
        return dlightNP
        
    def plight(self, node):
        plight = PointLight('plight')
        plight.setColor(VBase4(0.2, 0.2, 0.2, 1))
        plightNP = render.attachNewNode(plight)
        plightNP.setPos(node.getPos(self.mapRootNode))
        render.setLight(plightNP)
        return plightNP
    
    def chair(self, node):
        c = chair(self, node)
        self.mapObjects["static"].append(c)
        return c
    
    def playerPosition(self, node):
        self.player = playerController(self, None)
        self.player.setPos(node.getPos())
        self.player.setQuat(node.getQuat())
        
        return self.player