import sqlite3, sys
import sqlite_adapter as dbAdapter

sys.path.append("./insert_entities")
from insert_entities import InsertEntities
insertEntities = InsertEntities()

sys.path.append("./units")
#from worker import Worker
#worker = Worker()

#from simpleActor import SimpleActor

def loadTerrain(cursor):
  result = dbAdapter.fetchTerrain(cursor)
  #terrain = result[0]
  
  #insertEntities.insertTerrain(terrain)
  
  for i in range(0, len(result) ):
      terrain = result[i]
      insertEntities.insertTerrain(terrain)
  
def loadForrest(cursor):
  result = dbAdapter.fetchGridFlagForrestAll(cursor)
  
  for i in range(result[-1]):
    forrest = result[i]
    self.insertEntities.insertForrest(forrest)

def loadAllTrees(cursor):
  result = dbAdapter.fetchAllTrees(cursor)
  
  for i in range(0, len(result) ): #result[0][-1]): # result[-1] : last element (counted backwards)
    tree = result[i]
    insertEntities.insertTree(tree)
    
def loadAllBuildings(cursor):
  result = dbAdapter.fetchAllBuildings(cursor)
  
  #building_type = result[8]
  #path = dbAdapter.fetchBuildingPath(cursor, building_type)
  
  #result = result[:1]
  #result = result.append(path)
  
  for i in range(0, len(result) ):
    building = result[i]
    
    building_type = result[i][9]
    path = dbAdapter.fetchBuildingPath(cursor, building_type)
    
    building = building[:9]
    building = building + tuple(path)
    insertEntities.insertBuilding(building)
    
def loadAllActors(cursor):
  result = dbAdapter.fetchAllActors(cursor)
  
  for i in range(0, len(result) ):
    actor = result[i]
    #insertEntities.insertActor(actor)
    
    type = actor[1]
    if type == "worker":
        worker.loadWorker(actor)
    elif type == "soldier":
        pass

def loadEntities(cursor):
  loadTerrain(cursor)
  #loadForrest(cursor)
  #loadAllTrees(cursor)
  #loadAllBuildings(cursor)
  #loadAllActors(cursor)
  
