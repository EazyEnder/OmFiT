"""
Fiji script: Import omnipose files (outlines .txt) to trackmate using SpotROI

The outline file need to be named as: {FIELD}_{COLONY NUMBER}_phase_{TIME}_{MODEL EXTENDED NAME}_cp_outlines
{MODEL_EXTENDED_NAME} = {MODEL_NAME}_somestuff
Like: dt0_2_phase_0000_continuity1706_2000_3_cp_outlines
->FIELD is dt0; C_NUMBER is 2; TIME is 0000; and MODEL_NAME is continuity1706

"""

COLONY_NAME = "wt3Tc1"
DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#Keep the ROI Manager with all the ROIs
ALSO_OPEN_ROI_MANAGER = True
#If you just want to import ROIs to the ROI MANAGER, you can make the bool above True and the bool OPEN_TRACKMATE false
#Open TM or not, if False the script will just import the file ROIs to the manager
OPEN_TRACKMATE = False

#See at the end of the script to choose & import multiple models.

#-----------------------------------------------------------------

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

reload(sys)
sys.setdefaultencoding('utf-8')
logger = Logger.IJ_LOGGER

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def main(model_used = None):
	if OPEN_TRACKMATE:
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
			if OPEN_TRACKMATE:
				spot = SpotRoi.createSpot(X,Y,1.)
				model.addSpotTo(spot, int(time))
	if OPEN_TRACKMATE:
		model.endUpdate()
	
	imgs = []
	for f in argsort(unsorted_times):	
		imgs.append(IJ.openImage(unsorted_imgs_path[f]))

	stack = ImageStack(imgs[0].width,imgs[1].height)
	for img in imgs:
		stack.addSlice(img.getProcessor())
	
	imp = ImagePlus(COLONY_NAME + "_" + model_used,stack)
	if model_used is None:
		imp = ImagePlus(COLONY_NAME,stack)
	imp_dims = imp.getDimensions()
	imp.setDimensions(imp_dims[2], imp_dims[4], imp_dims[3]) 
	imp.show()
	
	fi = imp.getFileInfo()
	fi.directory = DATA_DIR
	imp.setFileInfo(fi)
	
	if ALSO_OPEN_ROI_MANAGER:
		rm = RoiManager.getInstance()
		IJ.run("Remove Overlay", "")
		rm.runCommand(imp,"Show All")
		rm.runCommand("Associate", "true")
		rm.runCommand("Show All")
	
	settings = Settings(imp)
	
	if OPEN_TRACKMATE:
		sm = SelectionModel(model)
		ds = DisplaySettingsIO.readUserDefault()
		
		displayer =  HyperStackDisplayer(model, sm, imp, ds)
		displayer.render()
		
		panelIdentifier = "ChooseTracker"
		trackmate = TrackMate(model, settings)
		sequence = TrackMateWizardSequence(trackmate, sm, ds)
		sequence.setCurrent(panelIdentifier)
		frame = sequence.run("TrackMate on " + imp.getShortTitle() )
		frame.setIconImage( Icons.TRACKMATE_ICON.getImage() )
		GuiUtils.positionWindow( frame, imp.getWindow() )
		frame.setVisible(True)

#You can choose the model_used if you have more than one outline file per image
main(model_used="continuity1706")