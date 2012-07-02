import sqlite3

def openConnection(level):
  connection = sqlite3.connect(str(level))#( "../levels/" + str(level) )
  cursor = connection.cursor()
  
  return connection, cursor
  
# write operations: #################################################################

def insertTree(connection, cursor, x, y, z, a, b, c, scale, path ):
  query = "INSERT INTO world ( x, y, z, a, b, c, scale, path ) VALUES ( ?, ?, ?, ?, ?, ?, ?, ? )"
  values = str(x), str(y), str(z), str(a), str(b), str(c), str(scale), str(path)
  cursor.execute(query, values)
  
  connection.commit()
  
def insertBuilding(connection, cursor, x, y, z, a, b, c, scale, path):
  query = "INSERT INTO building ( x, y, z, a, b, c, scale, path ) VALUES ( ?, ?, ?, ?, ?, ?, ?, ? )"
  values = str(x), str(y), str(z), str(a), str(b), str(c), str(scale), str(path)
  cursor.execute(query, values)
  connection.commit()
  
def insertGrid(connection, cursor, x, y, trespass, land, water, beach, swamp):
  query = "INSERT INTO grid ( x, y, trespass, land, water, beach, swamp ) VALUES ( ?, ?, ?, ?, ?, ?, ? )"
  values = str(x), str(y), str(trespass), str(land), str(water), str(beach), str(swamp)
  cursor.execute(query, values)
  connection.commit()
  
def updateGrid(connection, cursor, x, y, trespass):
  query = "UPDATE grid SET trespass=? where x=? AND y=?"
  values = str(trespass), str(x), str(y)
  cursor.execute(query, values)
  connection.commit()

# actor operations: #################################################################

def insertActor(connection, cursor, type, owner, health, x, y, z):
  query = "INSERT INTO actor ( type, owner, health, x, y, z ) VALUES ( ?, ?, ?, ?, ?, ? )"
  values = str(type), str(owner), str(health), str(x), str(y), str(z)
  cursor.execute(query, values)
  connection.commit()
  
def updateActor(connection, cursor, row_id, x, y, z):
  query = "UPDATE actor SET x=?, y=?, z=? WHERE row_id = ?"
  values = str(x), str(y), str(z), str(row_id)
  cursor.execute(query, values)
  connection.commit()
  
def selectActorInRectangle(cursor, x1, x2, y1, y2):
  # sortieren, n_x1 soll kleiner als n_x2 sein, bei y analog.
    if x1 <= x2:
        n_x1 = x1
        n_x2 = x2
    elif x1 > x2:
        n_x1 = x2
        n_x2 = x1
    if y1 <= y2:
        n_y1 = y1
        n_y2 = y2
    elif y1 > y2:
        n_y1 = y2
        n_y2 = y1
    
    values = n_x1, n_x2, n_y1, n_y2
    query = "SELECT row_id FROM actor WHERE x < ? AND x > ? AND y < ? AND y > ?"
    
    cursor.execute(query, values)
    result = cursor.fetchall()
    
    return result

def deleteActor(connection, cursor, row_id):
  query = "DELETE FROM actor WHERE row_id=?"
  values = str(row_id)
  cursor.execute(query, values)
  connection.commit()

# returns true if actor died, false otherwise
def actorGetDamage(connection, cursor, row_id, damage):
  query = "SELECT health FROM actor WHERE row_id=?"
  cursor.execute(query, row_id)
  result = cursor.fetchall()
  
  health = int(result[0]) - int(damage)
  
  if health < 0:
    print "sqlite_adapter.py.actorGetDamage.actorDied!"
    deleteActor(connection, cursor, row_id)
    return bool(1)
    
  values = str(health), str(row_id)
  query2 = "UPDATE actor SET health=? WHERE row_id=?"
  cursor.execute(query2, damage)
  
  connection.commit()
  
  return bool(0)
  
# read operations: ##################################################################
  
def fetchTerrain(cursor):
  query = "SELECT x, y, z, a, b, c, scale, path FROM world WHERE (name='terrain')"
  #query = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' UNION ALL SELECT name FROM sqlite_temp_master WHERE type IN ('table','view') ORDER BY 1"
  cursor.execute(query)
  result = cursor.fetchall()

  return result
  
def fetchXYMax(cursor):
  query = "SELECT xmax, ymax FROM world"
  cursor.execute(query)
  result = cursor.fetchall()
  
  return result
  
def fetchGridSize(cursor):
  query = "SELECT max(x), max(y) FROM grid"
  cursor.execute(query)
  result = cursor.fetchall()
    
  return result
  
def fetchAllTrees(cursor):
  query = "SELECT row_id, x, y, z, a, b, c, scale, path FROM world WHERE (name='tree')"
  cursor.execute(query)
  result = cursor.fetchall()
  
  return result
  
def fetchAllBuildings(cursor):
  query = "SELECT row_id, x, y, z, a, b, c, scale, health, type FROM building"
  cursor.execute(query)
  result = cursor.fetchall()
  
  return result
  
def fetchBuildingPath(cursor, building_type):
  query = "SELECT path from building_types WHERE type='" + building_type + "'"
  cursor.execute(query)
  result = cursor.fetchall()
  
  return result
  
def fetchAllActors(cursor):
  query = "SELECT row_id, type, owner, health, x, y, z FROM actor"
  cursor.execute(query)
  result = cursor.fetchall()
  
  return result

# werte der einzelnen einheitentypen abfragen

def fetchBuildingType(cursor, building_type):
    query = "SELECT path, anim_working, anim_attack, health, energy_need, factory, combattant, a, b, c, scale FROM building_types WHERE type=?"
    cursor.ecexute(query, building_type)
    result = cursor.fetchall()
    
    return result

def fetchBuildingTypeCombattant(cursor, building_type):
    query = "SELECT reload_time, attack_radius, attack_land, attack_air FROM building_types WHERE type=?"
    cursor.execute(query, building_type)
    
    return result

# einzelne Flags aus dem Grid abfragen: #############################################  

def fetchGridHelper(cursor, x, y, query):
  values = str(x), str(y)
  cursor.execute(query, values)
  result = cursor.fetchall()
  
  return bool(result)

def fetchGridFlagTrespass(cursor, x, y):
  query = "SELECT trespass FROM grid WHERE x=? AND y=?"
  values = str(x), str(y)
  cursor.execute(query, values)
  result = cursor.fetchall()
  return bool(result)

def fetchGridFlagLand(cursor, x, y):
  query = "SELECT land FROM grid WHERE x=? AND y=?"
  result = fetchGridHelper(cursor, x, y, query)
  return result

def fetchGridFlagWater(cursor, x, y):
  query = "SELECT water FROM grid WHERE x=? AND y=?"
  result = fetchGridHelper(cursor, x, y, query)
  return result

def fetchGridFlagBeach(cursor, x, y):
  query = "SELECT beach FROM grid WHERE x=? AND y=?"
  result = fetchGridHelper(cursor, x, y, query)
  return result

def fetchGridFlagSwamp(cursor, x, y):
  query = "SELECT swamp FROM grid WHERE x=? AND y=?"
  result = fetchGridHelper(cursor, x, y, query)
  return result

def fetchGridFlagForrest(cursor, x, y):
  query = "SELECT forrest FROM grid WHERE x=? AND y=?"
  result = fetchGridHelper(cursor, x, y, query)
  return result
  
def fetchGridFlagForrestAll(cursor):
  query = "SELECT x, y FROM grid WHERE forrest=true"
  result = cursor.execute(query)
  return result