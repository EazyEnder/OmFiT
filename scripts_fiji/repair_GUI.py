"""
Fiji script: An interface that allows the user to dynamically merge/divide cells or even remove a slice & preserving the json structure

The JSON need to have the same name as the parent folder and be in the same root of the imgs.

To repair a movie, you first need ... a movie. And not a random one, but a uniformised one. 
That's why the script "import_omnipose_to_trackmate" exists. Launch the script with the settings: OPEN_TRACKMATE = False & ALSO_OPEN_ROI_MANAGER = True.
"""

#Print errors in ImageJ Logger
LOG_ERROR = True
#Print errors & infos in ImageJ Logger
LOG = True

#Modify the json file when remove slice
MODIFY_JSON = True

# x <= 0 -> No auto save; Integer = Interval between each save
AUTO_SAVE = 0
#If None you'll need to have an img opened & the saves will have the img name (+ the suffix/index)
SAVE_NAME = None
#If None you'll need to have an img opened & the saves will be in the same folder of the img
SAVES_DIR = None

#SETTINGS FOR THE REPAIR TOOL
#Max where the algo will ascend to verify divisions
MAX_ANCESTOR = 8

ENABLE_DESCENDANT_VERIF = True
#Idem but down -> more sensitive. It is better to have errors than false corrections so 1 is good.
MAX_DESCENDANT = 4

#Minimum division direction score, if the score is too low then the cell will have a wrong cut so better to manually correct than have a correction that is false.
MINIMUM_SCORE = 0.8

#Is use when we'll find the interface between the two cells (in pixels)
#Also called epsilon 
GAP_MAX_RANGE = 10

#How the valid points in the division are weighted to the score.
#A higher weight means that the score will increase a lot with the number of good points in the new roi created
WEIGHT_GOOD_SCORE = 1.
#So for example we can make the weight of wrong points higher in order to find a better fit
WEIGHT_WRONG_SCORE = 2.5

#To find a direction we'll create a random angle and then, like a markov chain, search the maximum.
#MAX_TENTATIVES means the nbr of chains (if we find a good fit, we'll dont create new chains)
#MAX_CHAIN_STEPS is how much steps we'll make in the chain
MAX_TENTATIVES = 30
MAX_CHAIN_STEPS = 75

#The division part of the reparation will only try to correct cells in the interval
REPARATION_INTERVAL = None
#Save before and after the reparation with a specific suffix to the save file
SAVE_BEFOREANDAFTER_REPA = False
#--------------------------------------------------------

from javax.swing import JFrame, JButton, JOptionPane, JPanel
from java.awt import GridLayout
from ij import IJ, WindowManager as WM
import math

from ij.plugin.frame import RoiManager 
from ij.gui import Roi,PolygonRoi,ShapeRoi

from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Model, Spot
from fiji.plugin.trackmate.gui.wizard.descriptors import ChooseTrackerDescriptor
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui import Icons
from fiji.plugin.trackmate.gui import GuiUtils
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SpotRoi
from fiji.plugin.trackmate.gui.wizard import TrackMateWizardSequence
from fiji.plugin.trackmate.tracking.overlap import OverlapTrackerFactory, OverlapTracker
import os, sys
import json
import copy
from java.io import File
from random import random

def handleIMGError():
	imp = WM.getCurrentImage()
	if not(imp):
		print "Open an image first."
		if LOG or LOG_ERROR:
			IJ.log("Open an image first.")
		return False
	return True
	
def handleROIError():
	rm = RoiManager.getInstance()
	if not(rm):
		print "Open ROI Manager first."
		if LOG or LOG_ERROR:
			IJ.log("Open ROI Manager first.")
		return False
	return True


OPERATION_COUNTER = 0
LAST_SAVE_OP = 0

def autosave():
	global OPERATION_COUNTER
	global LAST_SAVE_OP
  	OPERATION_COUNTER += 1

	if AUTO_SAVE <= 0:
		return
	if not(OPERATION_COUNTER % AUTO_SAVE == 0):
		return
	if OPERATION_COUNTER == LAST_SAVE_OP:
		return
		
	save(None,suffix=str(OPERATION_COUNTER))
	LAST_SAVE_OP = OPERATION_COUNTER

#TODO: Improve the load function: also open the movie without previous removed frame instead of using the saved one
def load(event):
	filename = IJ.getFilePath("File that'll be loaded")
	if filename is None:
		print "Folder not found"
		if LOG or LOG_ERROR:
			IJ.log("Folder not found")
		return
	pure_name = filename.split("/")[-1]
	if not("txt" in pure_name.split(".")[-1]):
		print("The file need to be a txt file, are you sure this is the good one ?")
		if LOG or LOG_ERROR:
			IJ.log("The file need to be a txt file, are you sure this is the good one ?")
		return
	rm = RoiManager.getInstance()
	if not rm:
		rm = RoiManager()
	rm.reset()
	
	txt = open(filename, "r")
	for l in txt:
		line = l.split(":")[-1]
		positions_raw = line.split(",")
		i = 0
		X = []
		Y = []
		while i < len(positions_raw):
			if i+1 < len(positions_raw):
				X.append(int(positions_raw[i]))
				Y.append(int(positions_raw[i+1]))
			i += 2
		roi = PolygonRoi(X,Y,len(X),Roi.POLYGON)
		roi.setPosition(int(l.split(":")[0]))
		rm.addRoi(roi)
	txt.close()
	
def setSaveFolder(event):
	save_folder = IJ.getDirectory("Save Folder")
	global SAVES_DIR
	if not(save_folder is None):
		SAVES_DIR = save_folder

def save(event,suffix="manual"):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
  	
  	txt = None
  	filename = SAVE_NAME
  	if SAVE_NAME is None:
  		filename = imp.getTitle().split(".")[0]+"_save"
  	
  	if SAVES_DIR is None:
  		fi = imp.getOriginalFileInfo()
		directory = fi.directory
  		txt = open(os.path.join(directory,filename+"_"+suffix+".txt"),"w")
  	else:
  		txt = open(os.path.join(SAVES_DIR,filename+"_"+suffix+".txt"),"w")
  		
  	for roi in rm.getRoisAsArray():
		roi_slice = roi.getPosition()
		string = str(roi_slice) + ":"
		if type(roi) is ShapeRoi:
			roi = PolygonRoi(roi.getPolygon(),Roi.POLYGON)
			roi.setPosition(roi_slice)
		X = [int(x+roi.getBoundingRect().x) for x in roi.getXCoordinates()]
		Y = [int(y+roi.getBoundingRect().y) for y in roi.getYCoordinates()]
		for i in range(len(X)):
			if i != 0:
				string += ","
			string += str(X[i]) + "," + str(Y[i])
		txt.write(string+"\n")
	txt.close()
	
	print("Saved: "+suffix)
	if LOG:
		IJ.log("Saved: "+suffix)
	
def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)
    
def cleanROIs(event):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
	
	delete = 0	
	for i in range(rm.getCount()):
		roi = rm.getRoi(i-delete)
		if roi.getPosition()+1 > imp.getImageStack().getSize()+1:
			rm.select(i-delete)
			rm.runCommand(imp,"Delete")
			delete += 1
	print "Clean "+str(delete)+" ROIs"
	if LOG:
		IJ.log("Clean "+str(delete)+" ROIs")
  
def divide(event):  

	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return
	
	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
  
	selection = rm.getSelectedRoisAsArray()
	if not(len(selection) == 1) or len(selection) > 100:
	  	print "You need to select only 1 ROIs"
	  	if LOG or LOG_ERROR:
	  		IJ.log("You need to select only 1 ROIs")
	  	return
  	
	line = imp.getRoi()
	if not(line):
		print "You need to draw a line first"
		if LOG or LOG_ERROR:
			IJ.log("You need to draw a line first")
		return
	if not(line.isLine):
		print "Selection isn't a line"
		if LOG or LOG_ERROR:
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
		
		if angle > 3.1416:
			angle -= 2*3.1416
		
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
  
	autosave()
  
def merge(event):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
	
	selection = rm.getSelectedRoisAsArray()
	if len(selection) < 2 or len(selection) > 100:
		print "You need to select 2 ROIs at least"
		if LOG:
			IJ.log("You need to select 2 ROIs at least")
		return
	
	rm.runCommand('Combine')
	rm.runCommand('Add')
	rm.runCommand('Delete')
	if LOG:
		IJ.log("ROIs merged")
	print "ROIs merged"
	autosave()
	
def openTrackMate(event, preset_ROIs=None):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
		
	IJ.run("Show Overlay", "")
	IJ.run("Hide Overlay", "")
	IJ.run("Show Overlay", "")
	IJ.run("Remove Overlay", "")
	rm.runCommand(imp,"Show All")
		
	model = Model()
	model.setLogger(Logger.IJ_LOGGER)
	model.beginUpdate()
		
	ROIs = rm.getRoisAsArray()
	if not(preset_ROIs is None):
		ROIs = preset_ROIs
	for roi in ROIs:
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
	
def _getFlattenChildren(cell,cells):
	children = []
	for cellid in cell["children"]:
		children.append(cells[cellid])
		children.extend(_getFlattenChildren(children[-1],cells)) 
	return children	

def openTrackMateUsingROIs(event):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
		return
		
	selection = rm.getSelectedRoisAsArray()
	if len(selection) < 1 or len(selection) > 100:
		print "You need to select 1 ROI at least"
		if LOG:
			IJ.log("You need to select 1 ROI at least")
		return
	
	model = Model()
	model.setLogger(Logger.IJ_LOGGER)
	model.beginUpdate()
		
	for roi in rm.getRoisAsArray():
		roi_slice = roi.getPosition()
		if type(roi) is ShapeRoi:
			roi = PolygonRoi(roi.getPolygon(),Roi.POLYGON)
			roi.setPosition(roi_slice)
		spot = SpotRoi.createSpot([int(x+roi.getBoundingRect().x) for x in roi.getXCoordinates()],[int(y+roi.getBoundingRect().y) for y in roi.getYCoordinates()],10.)
		if math.isinf(spot.getDoublePosition(0)) or math.isnan(spot.getDoublePosition(0)) or math.isnan(spot.getDoublePosition(1)) or math.isinf(spot.getDoublePosition(1)):
			sx = 0
			i = 0
			for x in [int(x+roi.getBoundingRect().x) for x in roi.getXCoordinates()]:
				sx += x
				i += 1
			xc = sx/i
			sy = 0
			i = 0
			for y in [int(y+roi.getBoundingRect().y) for y in roi.getYCoordinates()]:
				sy += y
				i += 1
			yc = sy/i
			spot = Spot(xc, yc, 0., spot.getFeature(Spot.RADIUS), 10)
			spot.setRoi(SpotRoi([int(x+roi.getBoundingRect().x) for x in roi.getXCoordinates()],[int(y+roi.getBoundingRect().y) for y in roi.getYCoordinates()]))
		model.addSpotTo(spot, int(roi_slice-1))
	model.endUpdate()
	
	settings = Settings(imp)
	
	settings.trackerFactory = OverlapTrackerFactory()
	settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
	settings.trackerSettings['MIN_IOU'] = 0.05
	
	trackmate = TrackMate(model, settings)
	 
	ok = trackmate.execTracking()
	if not ok:
		print(str(trackmate.getErrorMessage()))
	
	cells = {}
	spots = model.getSpots()
	for i,spot in enumerate(spots.iterable(True)):
		frame = int(spot.getFeature("FRAME"))+1
		roi = spot.getRoi()
		X = [int(x+spot.getDoublePosition(0)) for x in roi.x if not(math.isnan(x))]
		Y = [int(y+spot.getDoublePosition(1)) for y in roi.y if not(math.isnan(y))]
		roi = PolygonRoi(X,Y,len(X),Roi.POLYGON)
		roi.setPosition(frame)
		cells[spot.getName()] = {
		"name": spot.getName(),
		"frame": frame,
		"center": (round(spot.getDoublePosition(0),2),round(spot.getDoublePosition(1),2)),
		"parent": None,
		"children": [],
		"roi": roi
		}

	
	trackIDs = model.getTrackModel().trackIDs(True)
	for id in trackIDs:
		edges = model.getTrackModel().trackEdges(id)
		for edge in edges:
			parent = str(edge).split(" : ")[0].split("(")[-1]
			child = str(edge).split(" : ")[1].split(")")[0]
			cells[parent]["children"].append(child)
			cells[child]["parent"] = parent

	cells_selected = []
	for roi in selection:
		for cellid in cells.keys():
			cell = cells[cellid]
			if roi.getPosition() != cell["frame"]:
				continue
				
			if not(roi.contains(int(cell["center"][0]),int(cell["center"][1]))):
				continue
				
			cells_selected.append(cell)
			break
			
	ROIs = []
	IDs = []
	for cell in cells_selected:
	
		parent = cell
		while not(parent["parent"] is None):
			parent = cells[parent["parent"]]
			if parent["name"] in IDs:
				break
			IDs.append(parent["name"])
			ROIs.append(parent["roi"])
		
		if not(cell["name"] in IDs):
			ROIs.append(cell["roi"])
			IDs.append(cell["name"])
			
		for cell in _getFlattenChildren(cell,cells):
			if not(cell["name"] in IDs):
				ROIs.append(cell["roi"])
				IDs.append(cell["name"])
		
	openTrackMate(None,preset_ROIs=ROIs)
	
def removeFrame(event):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return

	rm = RoiManager.getInstance()
	if not(handleROIError()):
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
		if colony_name == "":
			colony_name = directory.split("/")[-2]
		
		file_name = colony_name+".json"
		f = open(os.path.join(directory,file_name))
		data = json.load(f)
		
		for channel in data.keys():
			global_idx_offset = 0
			sorted_keys_indexes = argsort([int(nbr) for nbr in (data[channel].keys())])
			for index in [data[channel].keys()[ski] for ski in sorted_keys_indexes]:
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
			json.dump(data, outfile, indent=2)
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
	autosave()

def clearOperations(event):
	global OPERATION_COUNTER
	global LAST_SAVE_OP
	OPERATION_COUNTER = 0
	LAST_SAVE_OP = 0
	print("Operations counter reset to 0")
	if LOG:
		IJ.log("Operations counter reset to 0")
		
#/-------------------CUSTOM REPAIR ALGORITHM--------------------------/

def distTo(p1,p2):
	x = p2[0]-p1[0]
	y = p2[1]-p1[1]
	return math.sqrt(x**2+y**2)
def divideUsingLine(inter,dir,pts1,pts2):
	"""
		Divide points (pts1 + pts2) in two new groups separated by a line
		Return the two new groups and a score (relevant if pts1 and pts2 are not null/empty). 
			If the score is 0 then the new groups created are identics to the old ones.
	"""
	D = dir
	
	points = []
	points.extend(pts1)
	points.extend(pts2)
	
	new_pts_1 = []
	new_pts_2 = []
	angle_dir = math.atan2(D[1],D[0])
	for p in points:
		x = p[0]
		y = p[1]
		P = (x-inter[0],y-inter[1])
		angle = math.atan2(P[1], P[0])
		angle -= angle_dir
		
		if angle > 3.141:
			angle -= 2*3.141
		
		if angle < 0:
			new_pts_1.append((x,y))
		else:
			new_pts_2.append((x,y))
			
	score = 0
	for p in new_pts_1:
		if p in pts1:
			score += WEIGHT_GOOD_SCORE/ len(pts1)
		if p in pts2:
			score -= WEIGHT_WRONG_SCORE/ len(pts2)
	
	return (new_pts_1,new_pts_2,score)
	
def computeIntersection(cell1,cell2,frame=0):
	"""
		Return the intersection point and the division line (line that cuts the space in two sub-spaces with for each one a cell in it)
			(tuple, tuple)
	"""

	if cell1["frame"] != cell2["frame"]:
		print("Cant compute intersection between two cells because they are not presents at the same frame")
		return
	
	#max distance between two points (in pixels):
	epsilon = GAP_MAX_RANGE
	
	points = []
	for p1 in cell1["roi"]:
		for p2 in cell2["roi"]:
			dist = distTo(p1,p2)
			if dist > epsilon:
				continue
			if not(p1 in points):
				points.append(p1)
			if not(p2 in points):
				points.append(p2)
				
	if len(points) < 1:
		print("Cant compute intersection between two cells because no neighbors points found, try to increase the epsilon/gap max range")
		return
		
	x_sum = 0
	y_sum = 0
	for p in points:
		x_sum += p[0]
		y_sum += p[1]
	intersection = (x_sum/len(points),y_sum/len(points))
	

	precision = 0.1
	max_steps = MAX_CHAIN_STEPS
	iterations = 0
	
	angle = 0
	_,_,score = divideUsingLine(intersection,(math.cos(angle),math.sin(angle)),cell1["roi"],cell2["roi"])
	
	angle_logs = []
	while iterations < MAX_TENTATIVES and score<1.-precision:
	
		angle = 2*3.141*random()
		step = 0
		angle_step = 3.141*0.1
		dir_switch = True
		last_score = None
		while step < max_steps and score < 1.-precision:	
			step += 1
			_,_,score = divideUsingLine(intersection,(math.cos(angle),math.sin(angle)),cell1["roi"],cell2["roi"])
				
			if last_score is None:
				last_score = score
				continue
				
			if score < last_score:
				dir_switch = not(dir_switch)
				
			if dir_switch:
				angle += angle_step
			else:
				angle -= angle_step
				
			last_score = score
			
		angle_logs.append([angle,score])
		iterations += 1
		
	if score<1.-precision:
		max_arg = argsort([tpl[1] for tpl in angle_logs])[-1]
		angle = [tpl[0] for tpl in angle_logs][max_arg]
		score = [tpl[1] for tpl in angle_logs][max_arg]
		
	print("("+str(cell1["frame"]+1)+"->"+str(frame+1)+" | "+str(intersection)+") Div direction found after "+str(iterations)+" iterations and a score of "+str(score))
	if LOG:
		IJ.log("("+str(cell1["frame"]+1)+"->"+str(frame+1)+" | "+str(intersection)+") Div direction found after "+str(iterations)+" iterations and a score of "+str(score))
	if score < MINIMUM_SCORE:
		print("  |>  Score too low -> Cell division aborded")
		if LOG or LOG_ERROR:
			IJ.log("  |>  Score too low -> Cell division aborded")
		return None
	
	return ( intersection , (math.cos(angle),math.sin(angle)) )
	
def forceDivide(cells, new_cells,id,parentid,ancestor):
	
	child1 = cells[parentid]["children"][0]
	child2 = cells[parentid]["children"][1]
	for _ in range(ancestor-1):
		if not(len(cells[child1]["children"]) > 0 and len(cells[child2]["children"]) > 0):
			break
		child1 = cells[child1]["children"][0]
		child2 = cells[child2]["children"][0]
	
	
	tpl = computeIntersection(cells[child1],cells[child2],frame=cells[id]["frame"])
	if tpl is None:
		return new_cells
  	intersection, direction = tpl
  	
	cell = cells[id]
	ROI1, ROI2, _ = divideUsingLine(intersection, direction, cell["roi"], [])
	
	if not(ROI1 is None) and len(ROI1) > 3:
		new_cells[id+"c1"] = {
			"name": id+"c1",
			"frame": cell["frame"],
			"center": (0,0),
			"parent": None,
			"children": [],
			"roi": ROI1
		}
	if not(ROI2 is None) and len(ROI2) > 3:
		new_cells[id+"c2"] = {
			"name": id+"c2",
			"frame": cell["frame"],
			"center": (0,0),
			"parent": None,
			"children": [],
			"roi": ROI2
		}
	
	del new_cells[id]
	
	return new_cells
	
def forceMerge(cells):
	
	toModify = []
	for id in cells.keys():
		cell = cells[id]
		
		ancestor = 1
		if cell["parent"] is None:
			continue
		
		parent = cells[cell["parent"]]
		
		if len(parent["children"]) < 2:
			continue
		
		flag = False
		for childid in parent["children"]:
			if childid == id:
				continue
			child = cells[childid]
			if len(child["children"]) > 0:
				flag = True
				break
		if flag:
			continue
		
		flag = False
		while ancestor < MAX_ANCESTOR:
			if parent["parent"] is None:
				flag = True
				break
			parent = cells[parent["parent"]]
			ancestor += 1
			if len(parent["children"]) >= 2:
				flag = True
				break
		if flag:
			continue
		
		descendant = 1
		if len(cell["children"]) != 1:
			continue
		child = cells[cell["children"][0]]
		flag = False
		while descendant < 4:
			if len(child["children"]) != 1:
				flag = True
				break
			child = cells[child["children"][0]]
			descendant += 1
		if flag:
			continue
		
		toModify.append((id,ancestor,descendant))
		
	print(str(len(toModify)) + " merges found: " + str([str(tm[0])+"("+str(cells[tm[0]]["frame"]+1)+")" for tm in toModify]))
	if LOG:
		IJ.log(str(len(toModify)) + " merges found: " + str([str(tm[0])+"("+str(cells[tm[0]]["frame"]+1)+")" for tm in toModify]))
	
	deleted_cells = []
	for id,_,_ in toModify:
		if id in deleted_cells:
			continue
		cell = cells[id]
		roi = []
		ids_to_remove = []
		for childid in cells[cell["parent"]]["children"]:
			child = cells[childid]
			ids_to_remove.append(childid)
			roi.extend(child["roi"])
		
		cells[id+"merged"] = {
			"name": id+"merged",
			"frame": cell["frame"],
			"center": (0,0),
			"parent": cell["parent"],
			"children": cell["children"],
			"roi": roi
		}
		cells[cell["parent"]]["children"] = [id+"merged"]
		cells[cell["children"][0]]["parent"] = id+"merged"
		
		for idr in ids_to_remove:
			del cells[idr]
			deleted_cells.append(idr)

	return cells

def removeSporadicCells(cells):
	
	toRemove = []
	
	for id in cells.keys():
		cell = cells[id]
		
		if cell["parent"] is None and len(cell["children"]) <= 0:
			toRemove.append(id)
			continue
			
	print(str(len(toRemove)) + " sporadic cells found: " + str([str(tm)+"("+str(cells[tm]["frame"]+1)+")" for tm in toRemove]))
	if LOG:
		IJ.log(str(len(toRemove)) + " sporadic cells found: " + str([str(tm)+"("+str(cells[tm]["frame"]+1)+")" for tm in toRemove]))
	
	for id in toRemove:
		del cells[id]
	
	return cells

def correctTree(event):
	imp = WM.getCurrentImage()
	if not(handleIMGError()):
		return
		
	fi = imp.getOriginalFileInfo()
	directory = fi.directory
	colony_name = directory.split("/")[-1]
	if colony_name == "":
		colony_name = directory.split("/")[-2]
	model_name = imp.getTitle().split(".")[0].split("_")[-1]
	path = os.path.join(directory,colony_name+"_"+model_name+".xml")
	if not(os.path.exists(path)):
		string = "No xml file named as: {COLONY_NAME}_{MODEL_NAME}.xml found in the folder. Are you sure that you save trackmate tracking ?"
		print(string)
		if LOG or log_error:
			IJ.log(string)
		return

	file = File(path)
	reader = TmXmlReader( file )
	if not reader.isReadingOk():
	    sys.exit(reader.getErrorMessage())
	    
	model = reader.getModel()
	sm = SelectionModel(model)
	
	if SAVE_BEFOREANDAFTER_REPA:
		save(None,suffix="before_repa")
		
	#convert trackmate spots & tracks to custom objects : "cells"
	cells = {}
	spots = model.getSpots()
	rm = RoiManager.getInstance()
	if not rm:
		rm = RoiManager()

	for i,spot in enumerate(spots.iterable(True)):
	
		frame = int(spot.getFeature("FRAME"))
		roi = spot.getRoi()
		X = [int(x+spot.getDoublePosition(0)) for x in roi.x if not(math.isnan(x))]
		Y = [int(y+spot.getDoublePosition(1)) for y in roi.y if not(math.isnan(y))]
		roi = PolygonRoi(X,Y,len(X),Roi.POLYGON)
	
		cells[spot.getName()] = {
		"name": spot.getName(),
		"frame": frame,
		"center": (round(spot.getDoublePosition(0),2),round(spot.getDoublePosition(1),2)),
		"parent": None,
		"children": [],
		"roi": [(X[t], Y[t]) for t in range(len(X))]
		}

	
	trackIDs = model.getTrackModel().trackIDs(True)
	for id in trackIDs:
	    edges = model.getTrackModel().trackEdges(id)
	    for edge in edges:
	    	parent = str(edge).split(" : ")[0].split("(")[-1]
	    	child = str(edge).split(" : ")[1].split(")")[0]
	    	cells[parent]["children"].append(child)
	    	cells[child]["parent"] = parent
	    	
	#Remove sporadics cells
	cells = removeSporadicCells(cells)
	 
	#Merge cells that need to be merged
	cells = forceMerge(cells)
	    	
	#Where are the problems...
	new_cells = copy.deepcopy(cells)
	
	toModify = []
	modifications = 0
	for cellid in new_cells.keys():
		if not(cellid in new_cells.keys()):
			continue
		cell = new_cells[cellid]
		
		if not(REPARATION_INTERVAL is None) and not(cell["frame"]+1 >= REPARATION_INTERVAL[0] and cell["frame"]+1 <=REPARATION_INTERVAL[1]):
			continue
		
		if cell["parent"] is None:
			continue
		if cells[cell["parent"]]["parent"] is None:
			continue
		if len(cell["children"]) <= 0:
			continue
		
		#Get the ancestor
		parent_used = cells[cells[cell["parent"]]["parent"]]
		up_chi = parent_used["children"]
		last_up_id = cell["parent"]
		ancestor=2
		flag = False
		while(ancestor < MAX_ANCESTOR and not(flag)):
			if(len(up_chi) < 2):
				if(parent_used["parent"] is None):
				    flag = True
				    break
				ancestor += 1
				parent_used = cells[parent_used["parent"]]
				last_up_id = parent_used["name"]
				up_chi = parent_used["children"]
				if(len(up_chi)>=2):
				    break
			else:
			    break
		if flag:
			continue
		if(len(up_chi)<2):
			continue
			
		flag = False
		for child in up_chi:
			if child == last_up_id:
				continue
			
			cc = child
			for i in range(ancestor-1):
				if len(cells[cc]["children"]) <= 0:
					flag = True
					break
				cc = cells[cc]["children"][0]
			if flag:
				break
		if not(flag):
			continue


		if ENABLE_DESCENDANT_VERIF:
			child_used = cell
			descendant = 0
			while(descendant < MAX_DESCENDANT):
				if len(child_used["children"]) >= 2:
					break
				descendant += 1
				if len(child_used["children"]) == 0:
					break
				child_used = cells[child_used["children"][0]]
			if len(child_used["children"]) < 2 or len(child_used["children"]) == 0:
				continue

		toModify.append((cellid,parent_used["name"],ancestor))
		modifications += 1

	print(str(modifications) + " divisions found: " + str([str(tm[0])+"("+str(cells[tm[0]]["frame"]+1)+")" for tm in toModify]))
	if LOG:
		IJ.log(str(modifications) + " divisions found: " + str([str(tm[0])+"("+str(cells[tm[0]]["frame"]+1)+")" for tm in toModify]))


	for id,parentid,ancestor in toModify:
		new_cells = forceDivide(cells,new_cells,id,parentid,ancestor)
	
	#convert to ROIs
	rm.reset()
	for cellid in new_cells.keys():
		cell = new_cells[cellid]
		if cell is None:
			continue
		border = cell["roi"]
		roi = PolygonRoi([b[0] for b in border],[b[1] for b in border],len(border),Roi.POLYGON)
		roi.setPosition(cell["frame"]+1)
		rm.addRoi(roi)
		
	print("Repair done")
	if LOG:
		IJ.log("Repair done")
	
	if SAVE_BEFOREANDAFTER_REPA:
		save(None,suffix="after_repa")

	return	
			
#/--------------INTERFACE------------------/
frame = JFrame("Repair GUI", visible=True)  
divide_button = JButton("Divide", actionPerformed=divide)
merge_button = JButton("Merge", actionPerformed=merge)  
remove_frame_button = JButton("Remove frame", actionPerformed=removeFrame)  
open_trackmate_button = JButton("Open TrackMate", actionPerformed=openTrackMate)
save_button = JButton("Save", actionPerformed=save)
load_button = JButton("Load", actionPerformed=load)
set_savefolder_button = JButton("Set Save Folder", actionPerformed=setSaveFolder)
clear_button = JButton("Clear Op", actionPerformed=clearOperations)
correction_button = JButton("Live repair of cells (EXPERIMENTAL)", actionPerformed=correctTree)
open_selection_tm_button = JButton("Open TM using ROIs selection", actionPerformed=openTrackMateUsingROIs)
clean_button = JButton("Clean obsolete ROIs", actionPerformed=cleanROIs)

#Add a button to add a custom selection to ROI
#Add shortcut keys

panel = JPanel()
panel.add(divide_button)
panel.add(merge_button) 
panel.add(remove_frame_button)
panel.add(clean_button)

panel_tm = JPanel()
panel_tm.add(open_selection_tm_button)
panel_tm.add(open_trackmate_button)

panel_2 = JPanel()
panel_2.add(clear_button)
panel_2.add(save_button)
panel_2.add(load_button)
panel_2.add(set_savefolder_button)

panel_3 = JPanel()
panel_3.add(correction_button)

all_pan = JPanel(GridLayout(4, 1))
all_pan.add(panel)
all_pan.add(panel_tm)
all_pan.add(panel_2)
all_pan.add(panel_3)

frame.add(all_pan)
frame.pack() 