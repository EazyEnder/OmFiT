"""
Fiji script: Extract features from cells like ellipse fit, tracking, fluorescence... and export them in easily readable files
"""

COLONY_NAME = "wt5c2"
#Need to have a json file with the name of colony in the folder
DATA_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#Name of the model used when omnipose was applied (commonly in the name of multiple files in the folder)
MODEL_NAME = "continuity1706"

EXPORT_DIR = DATA_DIR


#x0,y0,x1,y1
BACKGROUND_RECT = [0,236,110,191]

SAVE_BACKGROUND_METADATA = True

#for spots features:
SAVE_FEATURES = False
SAVE_AS_TXT_FILE = True
SAVE_AS_JSON_FILE = False

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

#--------------------- PHASE & BASE PART------------------------------
reload(sys)
sys.setdefaultencoding('utf-8')

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
    	
if SAVE_FEATURES:	
	if SAVE_AS_JSON_FILE is None or SAVE_AS_JSON_FILE:
		cells_simp = copy.deepcopy(cells)
		for i in cells_simp.keys():
			if not("roi" in cells_simp[i].keys()):
				break
			del cells_simp[i]["roi"]
		with open(os.path.join(EXPORT_DIR,"spots_features.json"), "w") as outfile:
				json.dump(cells_simp, outfile)
	
	def line_builder(array):
		string = ""
		for a in array:
			string += str(a) + " "
		return string+"\n"
	
	if SAVE_AS_TXT_FILE:
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

if SAVE_BACKGROUND_METADATA:
	background_metadata_txt = open(os.path.join(EXPORT_DIR,"bg_metadata.txt"),"w")
	background_metadata_txt.write("FRAME X0 Y0 X1 Y1 MEAN VARIANCE \n")
means = []
variances = []
string = ""
for frame in range(ist.size()):
	ip = ist.getProcessor(frame+1)
	
	rect = BACKGROUND_RECT
	x0 = min(rect[0],rect[2])
	y0 = min(rect[1],rect[3])
	x1 = max(rect[0],rect[2])
	y1 = max(rect[1],rect[3])
	
	bg_sum = 0
	bg_sum_squared = 0
	N = int(x1-x0)*int(y1-y0)
	for x in range(int(x1-x0)):
		for y in range(int(y1-y0)):
			value = ip.getValue(int(x),int(y))
			bg_sum += value
			bg_sum_squared += value*value
	mean = bg_sum/N
	var = bg_sum_squared/N - mean*mean
	
	means.append(mean)
	variances.append(var)
	
	if SAVE_BACKGROUND_METADATA:
		string += str(frame+1) + " "
		string += str(x0) + " "
		string += str(y0) + " "
		string += str(x1) + " "
		string += str(y1) + " "
		string += str(mean) + " "
		string += str(var) + " \n"
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
	
	fluo_cells[cell_id] = {
		"raw_mean": raw_mean,
		"net_mean": net_mean
	}
print("Fluo intensity & features computed")
		
IJ.log(str(fluo_cells))
