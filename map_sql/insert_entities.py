from direct.showbase.DirectObject import DirectObject
from pandac import PandaModules as P

import grid_handler as GH

#from main_game import World

class InsertEntities(DirectObject):
    
    def insertTerrain(self, terrain):#(self, x, y, z, a, b, c, scale, model):
        #print terrain[0][0]
        
        #x=terrain[0][0]
        #y=terrain[0][1]
        #z=terrain[0][2]
        a=terrain[3]
        b=terrain[4]
        c=terrain[5]
        scale=terrain[6]
        model=str(terrain[7])
      
        terrain = loader.loadModel(str(model) + "-octree")
        #terrain.setPos(float(x), float(y), float(z))
        terrain.setHpr(float(a), float(b), float(c))
        terrain.setScale(float(scale))
        
        from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
        from pandac.PandaModules import OdeBody, OdeMass, OdeSphereGeom, OdePlaneGeom
        from pandac.PandaModules import *
        
        terrain.flattenLight()
        modelTrimesh = OdeTriMeshData(terrain, True)
        modelGeom = OdeTriMeshGeom(space, modelTrimesh)
        
        terrain.reparentTo(render)
        terrain.setCollideMask(P.BitMask32.bit(1))
        #terrain.setTag('myObjectTag', '1')
    
        terrain2 = loader.loadModel(model)
        #terrain2.setPos(float(x), float(y), float(z))
        terrain2.setHpr(float(a), float(b), float(c))
        terrain2.setScale(float(scale))
    
        terrain2.reparentTo(render)
        terrain2.setCollideMask(P.BitMask32.allOff())
    
        #return terrain
  
    def insertTree(self, tree):#(self, id, x, y, z, a, b, c, scale, model):
        id=tree[0]
        x=tree[1]
        y=tree[2]
        z=tree[3]
        a=tree[4]
        b=tree[5]
        c=tree[6]
        scale=tree[7]
        model=tree[8]
        
        tree = loader.loadModel(model)
        tree.setPos(float(x), float(y), float(z))
        tree.setHpr(float(a), float(b), float(c))
        tree.setScale(float(scale))
        
        tree.reparentTo(render)
        tree.setCollideMask(P.BitMask32.allOff())
        tree.setTag('markable', '1')
        tree.setTag("id", str(id))
        
        #return tree
    
    def insertForrest(self):
        pass
    
    def insertBuilding(self, building_attribs):#(self, id, koordsys, x, y, z, a, b, c, scale, model):
        #if koordsys == 1:
        #    x, y = GH.deNormalizer(x, y, 0, 0, 0, 0, 0)
        
        id, x, y, z, a, b, c, scale, health, model = building_attribs
        #id=building_attribs[0]
        #x=building_attribs[1]
        #y=building_attribs[2]
        #z=building_attribs[3]
        #a=building_attribs[4]
        #b=building_attribs[5]
        #c=building_attribs[6]
        #scale=building_attribs[7]
        #health=building_attribs[8]
        #model=building_attribs[9]
        
        x, y = GH.deNormalizer(x, y)
                
        building = loader.loadModel(model)
        building = building[0]
        building.setPos(float(x), float(y), float(z))
        building.setHpr(float(a), float(b), float(c))
        building.setScale(float(scale))
        
        building.reparentTo(render)
        building.setCollideMask(P.BitMask32.bit(0))
        building.setTag('markable', '1')
        building.setTag("id", str(id))
        