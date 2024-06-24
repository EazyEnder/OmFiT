"""
Fiji script: An interface that allows the user to dynamically merge/divide cells or even remove a slice & preserving the json structure
"""

from javax.swing import JFrame, JButton, JOptionPane, JPanel
from ij import IJ, WindowManager as WM
import math

from ij.plugin.frame import RoiManager 
from ij.gui import Roi,PolygonRoi,ShapeRoi

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
from fiji.plugin.trackmate import SpotRoi
from fiji.plugin.trackmate.gui.wizard import TrackMateWizardSequence
import os
import json

LOG = False
MODIFY_JSON = True

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)
  
def divide(event):  

  imp = WM.getCurrentImage()
  if not(imp):
  	print "Open an image first."
  	if LOG:
  		IJ.log("Open an image first.")
  	return
  	
  rm = RoiManager.getInstance()
  if not(rm):
  	print "Open ROI Manager first."
  	if LOG:
  		IJ.log("Open ROI Manager first.")
  	return
  
  selection = rm.getSelectedRoisAsArray()
  if not(len(selection) == 1):
  	print "You need to select only 1 ROIs"
  	if LOG:
  		IJ.log("You need to select only 1 ROIs")
  	return
  	
  line = imp.getRoi()
  if not(line):
  	print "You need to draw a line first"
  	if LOG:
  		IJ.log("You need to draw a line first")
  	return
  if not(line.isLine):
  	print "Selection isn't a line"
  	if LOG:
  		IJ.log("Selection isn't a line")
  	return
  
  D = (line.x2 - line.x1, line.y2 - line.y1)
  
  cell = selection[0]
  X = cell.getXCoordinates()
  Y = cell.getYCoordinates()
  
  ROI1_X = []
  ROI1_Y = []
  ROI2_X = []
  ROI2_Y = []
  angle_dir = math.atan2(D[1],D[0])
  for i in range(len(X)):
  	x = X[i]+cell.getBoundingRect().x
  	y = Y[i]+cell.getBoundingRect().y
  	P = (x-line.x1,y-line.y1)
  	angle = math.atan2(P[1], P[0]) - angle_dir
  	if angle < 0:
  		ROI1_X.append(x)
  		ROI1_Y.append(y)
  	else:
  		ROI2_X.append(x)
  		ROI2_Y.append(y)
  	
  ROI1 = PolygonRoi(ROI1_X,ROI1_Y,len(ROI1_X),Roi.POLYGON)
  ROI2 = PolygonRoi(ROI2_X,ROI2_Y,len(ROI2_X),Roi.POLYGON)
  
  slice_number = cell.getPosition()
  ROI1.setPosition(slice_number)
  ROI2.setPosition(slice_number)
  
  rm.runCommand('Delete')
  rm.addRoi(ROI1)
  rm.addRoi(ROI2)
  if LOG:
  	IJ.log("ROI divided")
  print "ROI divided"
  
def merge(event):
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG:
			IJ.log("Open an image first.")
		return
		
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG:
			IJ.log("Open ROI Manager first.")
		return
	
	selection = rm.getSelectedRoisAsArray()
	if len(selection) < 2:
		print "You need to select only 2 ROIs at least"
		if LOG:
			IJ.log("You need to select only 2 ROIs")
		return
	
	rm.runCommand('Combine')
	rm.runCommand('Add')
	rm.runCommand('Delete')
	if LOG:
		IJ.log("ROIs merged")
	print "ROIs merged"
	
def openTrackMate(event):
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG:
			IJ.log("Open an image first.")
		return
		
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG:
			IJ.log("Open ROI Manager first.")
		return
		
	IJ.run("Show Overlay", "")
	IJ.run("Hide Overlay", "")
	IJ.run("Show Overlay", "")
	IJ.run("Remove Overlay", "")
	rm.runCommand(imp,"Show All")
		
	model = Model()
	model.setLogger(Logger.IJ_LOGGER)
	model.beginUpdate()
		
	for roi in rm.getRoisAsArray():
		roi_slice = roi.getPosition()
		if type(roi) is ShapeRoi:
			roi = PolygonRoi(roi.getPolygon(),Roi.POLYGON)
			roi.setPosition(roi_slice)
		spot = SpotRoi.createSpot([int(x+roi.getBoundingRect().x) for x in roi.getXCoordinates()],[int(y+roi.getBoundingRect().y) for y in roi.getYCoordinates()],1)
		model.addSpotTo(spot, int(roi_slice-1))
	model.endUpdate()
	
	#imp_dims = imp.getDimensions()
	#imp.setDimensions(imp_dims[2], imp_dims[4], imp_dims[3]) 
	#imp.show()
	
	settings = Settings(imp)
	
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
	
def removeFrame(event):
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG:
			IJ.log("Open an image first.")
		return
		
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG:
			IJ.log("Open ROI Manager first.")
		return
		
	slice_index = imp.getCurrentSlice()
	IJ.run("Delete Slice", "")
	deleted = 0
	for i in range(rm.getCount()):
		roi = rm.getRoi(i-deleted)
		if roi.getPosition() == slice_index:
			rm.select(i-deleted)
			rm.runCommand(imp,"Delete")
			deleted += 1
		elif roi.getPosition() > slice_index:
			rm.select(i-deleted)
			rm.setPosition(roi.getPosition()-1)
	
	if MODIFY_JSON:
		fi = imp.getOriginalFileInfo()
		directory = fi.directory
		colony_name = directory.split("/")[-1]
		
		file_name = colony_name+".json"
		f = open(os.path.join(directory,file_name))
		data = json.load(f)
		
		for channel in data.keys():
			global_idx_offset = 0
			for index in data[channel].keys():
		 		gii = data[channel][index]["global_index"]
		 		index_to_keep = []
		 		for i in range(len(gii)):
		 			if slice_index == gii[i]+1:
		 				continue
		 			index_to_keep.append(i)
		 		for k in data[channel][index].keys():
		 			if "old_index" in k:
		 				continue
			 		if not("global_index" in k):
			 			data[channel][index][k] = [data[channel][index][k][i] for i in index_to_keep]
			 		else:
			 			if "old_index" in data[channel][index].keys():
			 				data[channel][index]["old_index"] = [data[channel][index]["old_index"][i] for i in index_to_keep]
			 				continue
			 			data[channel][index]["old_index"] = [data[channel][index][k][i] for i in index_to_keep]
			 	data[channel][index]["global_index"] = [i+global_idx_offset for i in range(len(index_to_keep))]
			 	global_idx_offset += len(index_to_keep)
		 		
	
		f.close()
		with open(os.path.join(directory,file_name), "w") as outfile:
			json.dump(data, outfile)
		print("JSON " + file_name + " modified")
	
	ite = 0
	while ite < 1000 and not(imp.getCurrentSlice() == slice_index):
		ite += 1
		if imp.getCurrentSlice() < slice_index:
			IJ.run(imp, "Next Slice [>]", "")
		else:
			IJ.run("Previous Slice [<]", "")
	
	if LOG:
		IJ.log("Frame "+str(slice_index)+" deleted")
	print("Frame "+str(slice_index)+" deleted")
			
		
	

#/--------------Interface------------------/
frame = JFrame("Repair GUI", visible=True)  
divide_button = JButton("Divide", actionPerformed=divide)
merge_button = JButton("Merge", actionPerformed=merge)  
remove_frame_button = JButton("Remove frame", actionPerformed=removeFrame)  
open_trackmate_button = JButton("Open TrackMate", actionPerformed=openTrackMate)
#Add a button to add a custom selection to ROI
#Add shortcut keys

panel = JPanel()
panel.add(divide_button)
panel.add(merge_button) 
panel.add(remove_frame_button) 
panel.add(open_trackmate_button)
frame.add(panel)
frame.pack() 