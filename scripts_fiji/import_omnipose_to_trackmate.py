"""
Fiji script: Import omnipose files (outlines .txt) to trackmate using SpotROI
"""

from fiji.plugin.trackmate import SpotRoi
import os
from ij import IJ, ImagePlus, ImageStack
from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate.gui.wizard.descriptors import ChooseTrackerDescriptor
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui import Icons
from fiji.plugin.trackmate.gui import GuiUtils
from fiji.plugin.trackmate import TrackMate
from java.io import File
import sys

from ij.plugin.frame import RoiManager 
from ij.gui import Roi,PolygonRoi

from fiji.plugin.trackmate.gui.wizard import TrackMateWizardSequence 

DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/wt3c12"

ALSO_OPEN_ROI_MANAGER = True

reload(sys)
sys.setdefaultencoding('utf-8')
logger = Logger.IJ_LOGGER

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def main(model_used = None):
	model = Model()
	model.setLogger(Logger.IJ_LOGGER)
	model.beginUpdate()
	
	unsorted_times = []
	unsorted_imgs_path = []
	
	f = 0
	for filename in (os.listdir(DATA_DIR)):
		if not("outlines" in filename and ".txt" in filename):
			continue
			
		ds_name = filename.split("_phase_")[0]
		if not(model_used is None):
			if not(filename.split("_")[4] == model_used):
				continue
		time = filename.split("_")[3]
		
		image_path = os.path.join(DATA_DIR,filename[:[i for i, ltr in enumerate(filename) if ltr == "_"][3]]+".tif")
		f += 1
		if(not(os.path.exists(image_path))):
			print("Image "+str(f)+" doesn't exist")
			continue
		unsorted_imgs_path.append(image_path)
		unsorted_times.append(time)
		
		outlines_file = open(os.path.join(DATA_DIR,filename), "r")
		for line in outlines_file:
			positions_raw = line.split(",")
			i = 0
			X = []
			Y = []
			while i < len(positions_raw):
				if i+1 < len(positions_raw):
					X.append(int(positions_raw[i]))
					Y.append(int(positions_raw[i+1]))
				i += 2
			if ALSO_OPEN_ROI_MANAGER:
				rm = RoiManager.getInstance()
				if not rm:
					rm = RoiManager()
				roi = PolygonRoi(X,Y,len(X),Roi.POLYGON)
				roi.setPosition(int(time)+1)
				rm.addRoi(roi)
			spot = SpotRoi.createSpot(X,Y,1.)
			model.addSpotTo(spot, int(time))
	model.endUpdate()
	
	imgs = []
	for f in argsort(unsorted_times):	
		imgs.append(IJ.openImage(unsorted_imgs_path[f]))

	stack = ImageStack(imgs[0].width,imgs[1].height)
	for img in imgs:
		stack.addSlice(img.getProcessor())
	
	imp = ImagePlus(model_used,stack)
	imp_dims = imp.getDimensions()
	imp.setDimensions(imp_dims[2], imp_dims[4], imp_dims[3]) 
	imp.show()
	
	if ALSO_OPEN_ROI_MANAGER:
		rm = RoiManager.getInstance()
		rm.runCommand("Associate", "true")
		rm.runCommand("Show All")
	
	settings = Settings(imp)
	
	sm = SelectionModel(model)
	ds = DisplaySettingsIO.readUserDefault()
	
	displayer =  HyperStackDisplayer(model, sm, imp, ds)
	displayer.render()
	
	panelIdentifier = "ChooseTracker";
	trackmate = TrackMate(model, settings)
	sequence = TrackMateWizardSequence(trackmate, sm, ds);
	sequence.setCurrent(panelIdentifier);
	frame = sequence.run("TrackMate on " + imp.getShortTitle() );
	frame.setIconImage( Icons.TRACKMATE_ICON.getImage() );
	GuiUtils.positionWindow( frame, imp.getWindow() );
	frame.setVisible(True);
			
main(model_used="continuity1706")