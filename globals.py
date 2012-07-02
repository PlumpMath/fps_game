from direct.gui.OnscreenImage import OnscreenImage
from pandac.PandaModules import TransparencyAttrib

crosshair = OnscreenImage(image = "./graphics/crosshairs/crosshair2.png", pos = (0, 0, 0), scale = (.03))
crosshair.setTransparency(TransparencyAttrib.MAlpha)

gravity = -100

objects = []

from system.odeWorldManager import *
#worldManager = odeWorldManager()
worldManager = None

stepSize = 1.0/60.0

jumpSpeed = 8.0

#map = None
player = None
socket = None

defaultShowCCD = False