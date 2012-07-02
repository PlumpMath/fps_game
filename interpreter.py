import globals, sys
from config import PLAYER_NAME, CONSOLE_TOGGLE_KEY, CONSOLE_SCROLL_UP_KEY, CONSOLE_SCROLL_DOWN_KEY, CONSOLE_PREVIOUS_COMMAND_KEY, CONSOLE_NEXT_COMMAND_KEY, CONSOLE_AUTOCOMPLETE_KEY

from system.map import *
from system.map_sql import *
import socket, thread
import commands

# note: every function called from the interpreter-method 
#has to return a string, witch is the console-output of this function

class cliClass(object):
    def __init__(self):
        self.map = None
        
        self.connected = False
        self.serverRunning = False
        #self.map = map_sql()
    
    def commandNotFound(self, value):
        return "command not found"
    
    def getCommands(self):
        commands = {
                    "commands" : self.printCommands,
                    
                    "bashrun" : self.bashrun,
                    
                    "credits" : self.credits,
                    "exit" : self.exit,
                    "destroyMap" : self.destroyMap,
                    "destroySQLMap" : self.destroySQLMap,
                    "dm" : self.destroySQLMap,
                    "quit" : self.exit,
                    
                    "getGravity" : self.getGravity,
                    "getMap" : self.getMap,
                    
                    "give" : self.give,
                    
                    "help" : self.help,
                    
                    "maps" : self.maps,
                    "noclip" : self.noclip,
                    
                    "pause" : self.pause,
                    
                    "setActor" : self.setActor,
                    "setCrosshair" : self.setCrosshair,
                    "setFrameRateMeter" : self.setFrameRateMeter,
                    "setGravity" : self.setGravity,
                    "setSQLMap" : self.setSQLMap,
                    "sm" : self.setSQLMap,
                    "setMap" : self.setMap,
                    "setRagdollDummy" : self.setRagdollDummy,
                    "showCCD" : self.showCCD,
                    
                    "whatismyip" : self.whatismyip,
                    "connect" : self.connect,
                    "startServer" : self.startServer,
                    "write" : self.write,
                    
                    "startSimulation" : self.startSimulation,
                    "stopSimulation" : self.stopSimulation,
                    
                    "unpause" : self.unpause,
                    
                    }
        
        return commands
        
    def interpreter(self, input):
        commands = self.getCommands()
        
        splitted = input.split(" ")
        command = splitted[0]
        try:
            value = splitted[1]
        except IndexError:
            value = -1
            
        try:
            return_value = commands.get(command, self.commandNotFound)(value)
        except ValueError, TypeError:
            return_value = "interpreter: unkown value"
        
        
        return return_value
        
    
    def credits(self, v):
        credits = """
    thanks to:
        
    Reto Spoerri
    rspoerri AT nouser.org
    http://www.nouser.org/
    (parts of this console)
        
        
        
        """
        return credits
    
    def bashrun(self, v):
        return str(commands.getoutput(v))
    
    def destroyMap(self, v):
        if v == "man":
            return "destroys the current map"
        try:
            result = self.map.destroy()
        except AttributeError:
            return "nothing to do"
        
        return result
    
    def destroySQLMap(self, v):
        print self.map
        #if self.map == None:
        #    return "nothing to do"
        #else:
        globals.map.destroy()
        
        return "SQLMap destroyed"
    
    def exit(self, v):
        if v == "man":
            return "quits the game"
        else:
            sys.exit()
        
    def getGravity(self, v):
        return "gravity: " + str(globals.gravity)
        #print globals.worldManager.getGravity()
        
    def getMap(self, v):
        if v == "man":
            return "returns the name of the current map"
        
    def give(self, v):
        if v == "man":
            return """
    gives the player the specified item:
    -1: take everything away
    0: all
    1: crowbar
    2: pistol
    3: mg
    4: shotgun
    5: grenade
    """
        return "not implemented yet"
    
    def help(self, v):
        help = """
    %s: toggle console
    %s:       scroll up
    %s:     scroll down
    %s:      previous command
    %s:    next command
        
    %s:           auto completion
    
    type ' commands ' for a list of all commands
    type <command> man for a simple man-page
    (e.g. 'maps man')
        """ % (CONSOLE_TOGGLE_KEY, CONSOLE_SCROLL_UP_KEY, 
               CONSOLE_SCROLL_DOWN_KEY, CONSOLE_PREVIOUS_COMMAND_KEY, 
               CONSOLE_NEXT_COMMAND_KEY, CONSOLE_AUTOCOMPLETE_KEY)
        return help
    
    def maps(self, v):
        if v == "man":
            man = """
    returns a list of all available maps
    use 'setMap <mapname>' for load a specific map"""
            
            return man
        
        import os
        maps = os.listdir("./maps")
        
        # formats the result to a list on the console
        map_list = ""
        for map in maps:
            map_list += str(map) + "\n"
        
        return map_list
    
    def noclip(self, v):
        import globals as globals
        globals.player.setFly(True, None, None)
        
        return "noclip switched"
    
    def pause(self, v):
        try:
            globals.worldManager.pause()
        except AttributeError:
            return "no world exists"
        return "paused"
    
    def printCommands(self, v):
        dict = self.getCommands()
        
        commands = sorted(dict.items())
        
        all_commands = ""
        line = ""
        for key in commands:#.iterkeys():#items():
            line = str(key).split(",")[0]
            all_commands += str(line[2:-1]) + "\n"
        return all_commands
        
    def setActor(self, v):
        actor = loader.loadModel("./models/terrain/lima2")
        actor.setScale(.04)
        actor.reparentTo(render)
        
        return "actor set"
        
    def setCrosshair(self, v):
        if v == "man":
            return """
    sets the crosshair to the specified value:
    0: crosshair off
    1: 
    2:
    
    """
        
        from direct.gui.OnscreenImage import OnscreenImage
        from pandac.PandaModules import TransparencyAttrib
        
        #if vars().has_key("v"):
        if v != -1:
            if int(v) == 0:
                globals.crosshair.destroy()
                #crosshair = OnscreenImage(image = "./models/crosshair_nothing.png", pos = (0, 0, 0))
                return "crosshair off"
            elif int(v) == 1:
                globals.crosshair.destroy()
                globals.crosshair = OnscreenImage(image = "./graphics/crosshairs/crosshair2.png", pos = (0, 0, 0), scale = (.03))
                globals.crosshair.setTransparency(TransparencyAttrib.MAlpha)
                
                return "crosshair set to 1"
            elif int(v) == 2:
                globals.crosshair.destroy()
                globals.crosshair = OnscreenImage(image = "./graphics/crosshairs/crosshair.png", pos = (0, 0, 0), scale = (.03))
                globals.crosshair.setTransparency(TransparencyAttrib.MAlpha)
                
                return "crosshair set to 2"
            else:
                return "unknown value: " + str(v)
        else:
            globals.crosshair.destroy()
            return "crosshair off"
    
    def setFrameRateMeter(self, v):
        if v == "man":
            return """
    0: frame meter off
    1: frame meter on
    """
        base.setFrameRateMeter(v) 
        return "set FrameRateMeter to: " +str(v)
        
    def setGravity(self, v):
        if v != -1:
            globals.worldManager.setGravity(float(v))
            
            return "gravity set to: " + str(v)
        else:
            globals.worldManager.setGravity(float(globals.gravity))
            return "gravity set to default (" + str(globals.gravity) +")"
            
    def setSQLMap(self, v):
        #globals.map_name = v
        globals.map = map_sql()
        globals.map.create()
        
        return "sqlite map loaded"
            
    def setMap(self, v):
        if v == "man":
            return """
    load the specified map
    use without the .py-extension of the map-files
    see 'maps' for a list of all available maps"""
        
        #from system.map import *
        #worldManager = odeWorldManager()
        self.map = map()
        self.map.create()
    
        return "copperode map loaded"
            
    def setRagdollDummy(self, v):
        pass
    
    def showCCD(self, v):
        print v
        if v == "man":
            return """
    visualize the continous collision detection
    1: True
    0: False
    """
        if v == "1":
            globals.defaultShowCCD = True
            return "showCCD set to True"
        elif v == "0":
            globals.defaultShowCCD = False
            return "showCCD set to False"
        else:
        #global defaultShowCCD
        #globals.map.defaultShowCCD = True
            return "unknown value"
    
    def startSimulation(self, v):
        globals.worldManager.startSimulation(globals.stepSize)
        return "simulation started"
        
    def stopSimulation(self, v):
        globals.worldManager.stopSimulation()
        return "simulation stopped"
        
    def unpause(self, v):
        try:
            globals.worldManager.unpause()
        except AttributeError:
            return "no world exists"
        return "unpaused"
    
    def whatismyip(self, v):
        return commands.getoutput("ifconfig").split("\n")[1].split()[1]
    
    def connect(self, ip):
        if self.serverRunning:
            return "unable to connect while Server is Running on this instance"
        elif self.connected:
            return "unable to connect while another connection is active"
        
        try:
            self.connected = True
            
            globals.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            globals.socket.connect((ip, 50000))
            
            globals.socket.send(PLAYER_NAME + " connected")
            
            return "connected to: "+str(ip)
        except socket.error:
            return "invalid destination"
    
    def receiveDataThread(self):
        while True:
            komm, addr = globalssocket.accept()
            while True:
                data = komm.recv(8192)
                
                if not data:
                    komm.close()
                    break
                
                print "[%s] %s" % (addr[0], data)
                print data
    
    def startServer(self, v):
        if self.serverRunning:
            return "server already running"
        elif self.connected:
            return "unable to start server while running another connection"
        
        self.serverRunning = True
        
        globals.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        globals.socket.bind(("", 50000))
        globals.socket.listen(1)
        
        thread.start_new_thread( globals.receiveDataThread, ())
        
        return "server started"
                
    def write(self, message):
        try:
            if message == "":
                message = " "
            globals.socket.send(message)
        
            return "sent message: "+str(message)
        except AttributeError:
            string = "\n maybe you should first 'connect' to an ip"
            return "unable to send message \n"+str(sys.exc_info())+string
        
    def sendPos(self, pos):
        try:
            globals.socket.send(str(pos[0]), 11)
        except AttributeError:
            return "unable to send position updates"