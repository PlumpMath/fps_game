import Image, ImageDraw, sys, math
sys.path.append("./sqlite_defs")
import sqlite_adapter as dbAdapter

def loadImageMap():
    # write to stdout
    #im.save(sys.stdout, "PNG")
    
    im = Image.open("./src/map.png")
    
    #draw = ImageDraw.Draw(im)
    #draw.line((0, 0) + im.size, fill=128)
    #draw.line((0, im.size[1], im.size[0], 0), fill=128)
    #im.show()
    
    x, y = im.size
    
    global matrix_bitmask
    
    matrix_bitmask = [[0 for i in xrange(x)] for i in xrange(y)]
    matrix_height = [[0 for i in xrange(x)] for i in xrange(y)]
    
    for i in range(0, x - 1): #nullpunkt auf der karte unten links
        for j in range(0, x - 1):
            r, g, b = im.getpixel((i, j))
            #print i, j
            matrix_bitmask[i][j] = r
            matrix_height[i][j] = b - 128 # bias, um auch negative hoehen speichern zu koennen
                    
    
    #print im.getpixel((30,30))
    #print matrix[10][1]
    #print matrix
    return x, matrix_bitmask, matrix_height

def normalizer(x, y, cursor):#xmin, xmax, ymin, ymax, grid_size): 
    #map_width = 1/(abs (min-x) + abs (max-x) );
    # map_koord -> 3d_koord:
    #threed_x = map_x / map_width + min-x
    
    xmax, ymax, grid_size = dbAdapter.fetchGridAttribs(cursor)
    
    xmin = xmax * -1
    ymin = ymax * -1
    
    #xmin = -200
    #xmax = 200
    #ymin = -200
    #ymax = 200
    #grid_size = 31
    
    # xnew: Betrag der Entfernung zwischen xmin und xmax
    xnew = math.fabs(xmax) + math.fabs(xmin)
    ynew = math.fabs(ymax) + math.fabs(ymin)
    
    x = x / (xnew / grid_size)
    y = y / (ynew / grid_size)
    
    # nullpunkt von der Mitte nach oben links verschieben
    x = x + (grid_size / 2) + .5
    #y = math.fabs(y - (grid_size / 2) - .5)
    # nullpunkt doch lieber nach links UNTEN verschieben
    y = y + (grid_size / 2) + .5
    
    #print "normalizer:"
    #print math.ceil(x), math.ceil(y)
    #print int(x), int(y)
    
    # werte runden, bzw. auch nicht
    return int(x), int(y), x, y

#get the koords in the 3d-world:
def deNormalizer(x, y):
    #xmax, ymax, grid_size = dbAdapter.fetchGridAttribs(cursor)
    
    #xmin = xmax
    #ymin = ymax
    
    xmin = -200
    xmax = 200
    ymin = -200
    ymax = 200
    grid_size = 31
    
    xnew = math.fabs(xmax) + math.fabs(xmin)
    ynew = math.fabs(ymax) + math.fabs(ymin)
    
    x = ( x * ( xnew / grid_size) ) - (xnew / 2)
    y = ( y * ( ynew / grid_size) ) - (ynew / 2)
    
    # noch eine halbe kaestchenweite aufaddieren, um in die mitte der rasterkaestchen zu kommen
    x = x + ((xnew/grid_size) / 2)
    y = y + ((ynew/grid_size) / 2)
    
    #x = x / 
    
    #x = (xnew / grid_size) * x
    #y = (ynew / grid_size) * y
    
    return x, y
    
def heightCalculator(x, y):
    return h

def gridHandler():
    pass

# Gibt zu einer gegebenen Koordinate der 3d-Welt den zugehoerigen Quadraten des Grid zurueck
def getRectangle(x, y):
    
    
    
    
    return grid_x, grid_y
