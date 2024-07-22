"""
Fiji script: Extract features from cells like ellipse fit, tracking, fluorescence... and export them in easily readable files

Steps:
1 - Need to have channels movies: {COLONY_NAME}_y.tif & {COLONY_NAME}_r.tif & {COLONY_NAME}_{MODEL_NAME}.tif
	You can update previous stacks (like r & y) using the script named: "update_stack_using_json"
2 - Rename theses channels movies to the good format (like above)
3 - Change the background rectangle used in this script (see below) by looking at the yellow fluo movie
4 - Launch this script, get the json files and have fun...

Think to rename all channels files like wt3c10 not wt3_10
Don't switch Image window during the roi process
If you have a file not found error, verifify if the disk is bounted, or verify if the two fluo movies exists in the folder with a name like wt1c2
"""

COLONY_NAME = "wt3Tc1"
#Need to have a json file with the name of colony in the folder
DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#Name of the model used when omnipose was applied (commonly in the name of multiple files in the folder)
MODEL_NAME = "continuity1706"

EXPORT_DIR = DATA_DIR

#If the json files exists, we'll use it -> so we compute only the tracks
USE_FILES_IF_EXIST = False


#x0,y0,x1,y1 - DON'T FORGET TO CHANGE IT
BACKGROUND_RECT = [0,276,124,276+58]

SAVE_BACKGROUND_METADATA = True

#for spots features:
SAVE_SPOTS_FEATURES = True
SAVE_SPOTS_AS_TXT_FILE = False
SAVE_SPOTS_AS_JSON_FILE = True

#for fluo features:
SAVE_FLUO_FEATURES = True
SAVE_FLUO_AS_JSON_FILE = True

SAVE_TRACKS = True

#---------------------------------------------------------------------

from ij import IJ, ImagePlus, ImageStack

from fiji.plugin.trackmate.visualization.hyperstack import HyperStackDisplayer
from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from java.io import File
from ij.plugin.frame import RoiManager 
from ij.gui import Roi,PolygonRoi
import sys, os, json, copy
from ij.measure import ResultsTable

FILES_EXISTS = False
if USE_FILES_IF_EXIST:
	FILES_EXISTS = os.path.exists(os.path.join(EXPORT_DIR,"spots_features.json")) and os.path.exists(os.path.join(EXPORT_DIR,"fluo_features.json"))

reload(sys)
sys.setdefaultencoding('utf-8')

if not(FILES_EXISTS):
	
	file = File(os.path.join(DATA_DIR,COLONY_NAME+"_"+MODEL_NAME+".xml"))
	logger = Logger.IJ_LOGGER
	reader = TmXmlReader( file )
	if not reader.isReadingOk():
	    sys.exit(reader.getErrorMessage())
	    
	model = reader.getModel()
	sm = SelectionModel(model)
	
	file_name = COLONY_NAME+".json"
	f = open(os.path.join(DATA_DIR,file_name))
	data = json.load(f)
	f.close()
	
	global_indexes = []
	times = []
	for index in data[data.keys()[0]].keys():
		for time in data[data.keys()[0]][index]["delta_t"]:
			times.append(time)
		for gii in data[data.keys()[0]][index]["global_index"]:
			global_indexes.append(gii)
	def argsort(seq):
	    return sorted(range(len(seq)), key=seq.__getitem__) 
	    
	sorted_indexes = argsort(global_indexes)
	times = [times[s] for s in sorted_indexes]
	
	cells = {}
	
	spots = model.getSpots()
	IJ.run("Set Measurements...", "fit display add redirect=None decimal=3")
	rm = RoiManager.getInstance()
	if not rm:
		rm = RoiManager()
	imp = IJ.createImage("Untitled", "8-bit white", 512, 512, 1)
	imp.show()
	for i,spot in enumerate(spots.iterable(True)):
	
		frame = int(spot.getFeature("FRAME"))
		roi = spot.getRoi()
		
		rm.reset()
		X = [int(x+spot.getDoublePosition(0)) for x in roi.x]
		Y = [int(y+spot.getDoublePosition(1)) for y in roi.y]
		roi = PolygonRoi(X,Y,len(X),Roi.POLYGON)
		rm.addRoi(roi)
		rm.select(0)
		
		IJ.run(imp, "Measure", "")
		table = ResultsTable.getResultsTable()
		major = table.getValue("Major",0)
		minor = table.getValue("Minor",0)
		angle = table.getValue("Angle",0)
		table.deleteRow(0)
	
		cells[spot.getName()] = {
		"frame": frame,
		"time": times[frame],
		"center": (round(spot.getDoublePosition(0),2),round(spot.getDoublePosition(1),2)),
		"parent": None,
		"children": [],
		"ellipse":(round(major,2),round(minor,2),round(angle,2)),
		"pixels": [(p.x,p.y) for p in roi.getContainedPoints()],
		}
		
	rm.close()
	imp.close()
	IJ.selectWindow("Results")
	IJ.run("Close")
	
	print("Cells features computed")
	
	trackIDs = model.getTrackModel().trackIDs(True)
	for id in trackIDs:
	    edges = model.getTrackModel().trackEdges(id)
	    for edge in edges:
	    	parent = str(edge).split(" : ")[0].split("(")[-1]
	    	child = str(edge).split(" : ")[1].split(")")[0]
	    	cells[parent]["children"].append(child)
	    	cells[child]["parent"] = parent
	    	
	if SAVE_SPOTS_FEATURES:	
		if SAVE_SPOTS_AS_JSON_FILE is None or SAVE_SPOTS_AS_JSON_FILE:
			cells_simp = copy.deepcopy(cells)
			for i in cells_simp.keys():
				if not("roi" in cells_simp[i].keys()):
					break
				del cells_simp[i]["roi"]
			with open(os.path.join(EXPORT_DIR,"spots_features.json"), "w") as outfile:
					json.dump(cells_simp, outfile, indent=2)
		
		def line_builder(array):
			string = ""
			for a in array:
				string += str(a) + " "
			return string+"\n"
		
		if SAVE_SPOTS_AS_TXT_FILE:
			main_txt = open(os.path.join(EXPORT_DIR,"spots_features.txt"),"w")
			prefix = ["ID"]
			rslt_matrix = []
			for index in cells.keys():
				values = [index]
				for key in cells[index].keys():
					if "roi" in key:
						continue
					if not(key in prefix):
						prefix.append(key)
					values.append(cells[index][key])
				rslt_matrix.append(values)
			print rslt_matrix
			main_txt.write(line_builder(prefix))
			for line in rslt_matrix:
				main_txt.write(line_builder(line))
			main_txt.close()
		print("Cells features saved")
		
	#----------------------FLUO PART-------------------------------
	imp = IJ.openImage(os.path.join(DATA_DIR,COLONY_NAME+"_y.tif"))
	ist = imp.getImageStack()
	
	imp_r = IJ.openImage(os.path.join(DATA_DIR,COLONY_NAME+"_r.tif"))
	ist_r = imp_r.getImageStack()
	
	if SAVE_BACKGROUND_METADATA:
		background_metadata_txt = open(os.path.join(EXPORT_DIR,"bg_metadata.txt"),"w")
		background_metadata_txt.write("FRAME X0 Y0 X1 Y1 MEAN VARIANCE MEAN_R VARIANCE_R \n")
	means = []
	variances = []
	means_r = []
	variances_r = []
	string = ""
	for frame in range(ist.size()):
		ip = ist.getProcessor(frame+1)
		ip_r = ist_r.getProcessor(frame+1)
		
		rect = BACKGROUND_RECT
		x0 = min(rect[0],rect[2])
		y0 = min(rect[1],rect[3])
		x1 = max(rect[0],rect[2])
		y1 = max(rect[1],rect[3])
		
		bg_sum = 0
		bg_sum_squared = 0
		bg_sum_r = 0
		bg_sum_squared_r = 0
		N = int(x1-x0)*int(y1-y0)
		for x in range(int(x1-x0)):
			for y in range(int(y1-y0)):
				value = ip.getValue(int(x),int(y))
				value_r = ip_r.getValue(int(x),int(y))
				bg_sum += value
				bg_sum_squared += value*value
				bg_sum_r += value_r
				bg_sum_squared_r += value_r*value_r
		mean = bg_sum/N
		var = bg_sum_squared/N - mean*mean
		mean_r = bg_sum_r/N
		var_r = bg_sum_squared_r/N - mean_r*mean_r
		
		means.append(mean)
		variances.append(var)
		means_r.append(mean_r)
		variances_r.append(var_r)
		
		if SAVE_BACKGROUND_METADATA:
			string += str(frame+1) + " "
			string += str(x0) + " "
			string += str(y0) + " "
			string += str(x1) + " "
			string += str(y1) + " "
			string += str(mean) + " "
			string += str(var) + " "
			string += str(mean_r) + " "
			string += str(var_r) + " \n"
	if SAVE_BACKGROUND_METADATA:
		background_metadata_txt.write(string)
		background_metadata_txt.close()
	print("Background intensity computed")
	
	fluo_cells = {}
	for cell_id in cells.keys():
		cell = cells[cell_id]
		raw_sum = 0
		ip = ist.getProcessor(cell["frame"]+1)
		for pixel in cell["pixels"]:
			x = pixel[0]
			y = pixel[1]
			raw_sum += ip.getValue(int(x),int(y))
		raw_mean = raw_sum / len(cell["pixels"])
		net_mean = raw_mean - means[cell["frame"]]
		
		raw_sum_r = 0
		ip_r = ist_r.getProcessor(cell["frame"]+1)
		for pixel in cell["pixels"]:
			x = pixel[0]
			y = pixel[1]
			raw_sum_r += ip_r.getValue(int(x),int(y))
		raw_mean_r = raw_sum_r / len(cell["pixels"])
		net_mean_r = raw_mean_r - means_r[cell["frame"]]
		
		fluo_cells[cell_id] = {
			"raw_mean": raw_mean,
			"net_mean": net_mean,
			"raw_mean_r":raw_mean_r,
			"net_mean_r":net_mean_r
		}
	print("Fluo intensity & features computed")
			
	if SAVE_FLUO_FEATURES:	
		if SAVE_FLUO_AS_JSON_FILE is None or SAVE_FLUO_AS_JSON_FILE:
			fluo_cells_simp = copy.deepcopy(fluo_cells)
			with open(os.path.join(EXPORT_DIR,"fluo_features.json"), "w") as outfile:
					json.dump(fluo_cells_simp, outfile, indent=2)
	print("Fluo features saved")
	
else:
	f = open(os.path.join(EXPORT_DIR,"spots_features.json"))
	cells = json.load(f)
	f.close()
	f = open(os.path.join(EXPORT_DIR,"fluo_features.json"))
	fluo_cells = json.load(f)
	f.close()

def getEndingCells(cells):
	ending_cells = []
	for cell_id in cells.keys():
		cell = cells[cell_id]
		if cell["children"] is None or len(cell["children"]) == 0:
			ending_cells.append(cell_id)
	return ending_cells

def getTrajectory(cells,cell_id):
	parent = cells[cell_id]["parent"]
	cells_branch = [cell_id]
	while not(parent is None):
		cells_branch.insert(0,parent)
		parent = cells[parent]["parent"]
	return cells_branch

if SAVE_TRACKS:
	ending_cells = getEndingCells(cells)
	for i,cellid in enumerate(ending_cells):
		traj = getTrajectory(cells,cellid)
		
		track_txt = open(os.path.join(EXPORT_DIR,"track_De"+cellid+"_An"+traj[0]+".txt"),"w")
		track_txt.write("TIME SIZE YFP RFP \n")
		
		yfp = [fluo_cells[t]["net_mean"] for t in traj]
		rfp = [fluo_cells[t]["net_mean_r"] for t in traj]
		time = [cells[t]["time"] for t in traj]
		size = [cells[t]["ellipse"][0] for t in traj]
		
		string = ""
		for j in range(len(traj)):
			string += str(time[j])+" "
			string += str(size[j])+" "
			string += str(yfp[j])+" "
			string += str(rfp[j])+"\n"
			
		track_txt.write(string)
		track_txt.close()
		
		print("Save track: "+str(i+1)+"/"+str(len(ending_cells)))
	
