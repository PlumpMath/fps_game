from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", """sync-video 0
fullscreen 1
win-size 1920 1080
yield-timeslice 0 
client-sleep 0 
multi-sleep 0
basic-shaders-only #t

audio-library-name null""")

from direct.directbase import DirectStart
from system.map import *

from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenText import OnscreenText
import sys, gc

from console.panda3d_console import panda3dIOClass

render.setShaderAuto()
#base.toggleWireframe()
base.setFrameRateMeter(True)
base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())

"""
Just for the sake of the demo -- quickly set showing ccd process visualization
"""
defaultShowCCD = False

"""
Good practice for the time of development
"""
gc.enable()
gc.set_debug(gc.DEBUG_LEAK)

class main(object):
	def __init__(self):
		base.setBackgroundColor(.2, .2, .2)
		base.camLens.setFov(75)
		base.camLens.setNear(0.01)
		base.disableMouse()
		
		base.setFrameRateMeter(True)
		render.setShaderAuto()
		self.console = panda3dIOClass(self)
		
#		self.cross = DirectFrame(
#			frameSize = (-.5, .5, -.5, .5),
#			scale = 0.02,
#			frameColor = Vec4(0, 0, 0, 1),
#			)
		
		self.heldIcon = DirectFrame(
			parent = base.a2dBottomRight,
			pos = (-0.25, 0, 0.2),
			frameSize = (-0.2, 0.2, -.14, .14),
			scale = 1.0,
			frameColor = Vec4(0, 0, 0, 1),
			)
		
		
		
		self.map = map()
		global defaultShowCCD
		self.map.defaultShowCCD = defaultShowCCD
		
		base.accept("update_hud", self.updateHud)
		base.accept("clear_hud", self.clearHud)
		
	def updateHud(self, icon):
		if icon is not None:
			self.heldIcon["image"] = icon
			self.heldIcon["image_scale"] = (0.2, 0, 0.14)
	
	def clearHud(self):
		self.heldIcon["image"] = None
	
	def hideText(self):
		if self.textObjectVisisble:
			self.textObject.detachNode()
			self.textObjectVisisble = False
		else:
			self.textObject.reparentTo(aspect2d)
			self.textObjectVisisble = True
	
#	def startGame(self):
#		self.map.create()
	
	def doExit(self):
		self.map_sql.destroy()
		
		print "\n\n\nGARBAGE COLLECTED:\n"
		gc.collect()
		for g in gc.garbage:
			print g
		
		sys.exit()

m = main()
#m.startGame()

base.accept("escape", m.doExit)

run()
