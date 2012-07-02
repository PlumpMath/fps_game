import sqlite3, os, sys

def openConnection():
    connection = sqlite3.connect("./level_fps0.db")
    cursor = connection.cursor()
    
    return connection, cursor

def createTable(cursor):
    cursor.execute("create table map ( name text, path text, scale integer, x integer, y integer, z integer, h integer, p integer, r integer )")

def insertGround(cursor):
    query = "insert into map ( name, path, scale, x, y, z, h, p, r ) values ( ?, ?, ?, ?, ?, ?, ?, ?, ? )"
    values = "ground", "./models/terrain/grass2", 20, 0, 0, 0, 0, 0, 0
    cursor.execute(query, values)
    
    return cursor

print("deleting existing database file")
exist = os.access("./level_fps0.db", os.F_OK)

if exist:
    os.system("rm ./level_fps0.db")

connection, cursor = openConnection()

print("createTable")
createTable(cursor)
print("done")

print("insertGround")
insertGround(cursor)
print("done")

connection.commit()
cursor.close()

print("done")