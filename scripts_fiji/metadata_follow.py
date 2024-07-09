"""
Fiji script: Follow ROIs using metadatas files and export them

Not finished(script not working) bcs metadata files doesn't contain all the moves
"""

#Field
POSITION = "wt4"
#Path to the tif files & crops.csv & json (if present)
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/march15/"+POSITION+"/"
#Path to te metadata common root folder
METADATA_PATH = "/media/irina/LIPhy-INFO/cyano/march15/"

#Column index of the X positions
ROI_CSV_OFFSET = 2

#microms corresponding to 1 pixel
CALIBRATION_um_px = 0.1

#-----------------------------------------------------------

import os,sys 
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
import json 
import csv
from datetime import datetime

reload(sys)
sys.setdefaultencoding('utf-8')

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def getCropsROIs():
	path = os.path.join(DIR_PATH,"crops.csv")
	if not(os.path.exists(path)):
		print(path+" does not exist")
		return
	#[(POSITION X & Y),(SIZE WIDTH & HEIGHT)],[...]
	crops = []
	with open(path) as csvfile:
		spamreader = csv.reader(csvfile, delimiter=',')
		for i,row in enumerate(spamreader):
			if i == 0:
				continue
			if len(row) < 5:
				continue
			x = int(row[ROI_CSV_OFFSET])
			y = int(row[ROI_CSV_OFFSET+1])
			width = int(row[ROI_CSV_OFFSET+2])
			height = int(row[ROI_CSV_OFFSET+3])
			crops.append([(x,y),(width,height)])
	return crops
CROPS = getCropsROIs()

def readMetadata():
	root = METADATA_PATH
	if not(os.path.exists(root)):
		print(root +" does not exist")
		return
	
	mds_list = []
	for i,filename in enumerate(os.listdir(root)):
		path = os.path.join(root,filename)
		if not(os.path.isdir(path)):
			continue
		for j, filename2 in enumerate(os.listdir(path)):
			path2 = os.path.join(path,filename2)
			if not(os.path.isdir(path2)):
				continue
			if not(os.path.exists(os.path.join(path2,"metadata.txt"))):
				continue
			md_path = os.path.join(path2,"metadata.txt")
			
			data = {}
			
			sourceEncoding = "iso-8859-1"
			targetEncoding = "utf-8"
			src = open(md_path)
			tar = open(md_path.split(".")[-2]+"_converted.json", "w")
			
			tar.write(unicode(src.read(), sourceEncoding).encode(targetEncoding))
			tar.close()
			src.close()
			
			with open(md_path.split(".")[-2]+"_converted.json", 'r') as f:
				data = json.load(f)
			data = data["Summary"]
			
			position = None
			for pos in data["StagePositions"]:
				if pos["Label"] == POSITION:
					for device in pos["DevicePositions"]:
						if device["Device"]=="XYStage":
							position = device["Position_um"]
							for p in range(len(position)):
								position[p] = float(position[p])/CALIBRATION_um_px
							break
					break
			
			frame_count = int((len(os.listdir(path2))-1)/3)
			mds_list.append((data["StartTime"],position,frame_count))
			break
	
	#ex: "2024-03-18 12:28:29.969 +0100"
	raw_dates = [tpl[0] for tpl in mds_list]
	times = []
	for rd in raw_dates:
	
		splt = rd.split(" ")
		year = int(splt[0].split("-")[0])
		month = int(splt[0].split("-")[1])
		day = int(splt[0].split("-")[2])
		hour = int(splt[1].split(":")[0])
		mins = int(splt[1].split(":")[1])
		sec = int(splt[1].split(":")[2].split(".")[0])
		ms = int(splt[1].split(":")[2].split(".")[1])
	
		times.append((datetime(year,month,day,hour,mins,sec,ms)-datetime(1970,1,1)).total_seconds())
	sorted_indexes = argsort(times)
	sorted_mds = [mds_list[i] for i in sorted_indexes]
	
	counts = [tpl[2] for tpl in sorted_mds]
	inds_begin = [0]
	for i,c in enumerate(counts):
		if i == len(counts)-1:
			break
		inds_begin.append(inds_begin[-1]+c)
		
	positions = [tpl[1] for tpl in sorted_mds]
	delta_pos = []
	pos_ref = positions[-1]
	for p in positions:
		delta_pos.append((p[0]-pos_ref[0],p[1]-pos_ref[1]))
	
	mds = []
	for i in range(len(times)):
		mds.append((times[i],delta_pos[i],counts[i],inds_begin[i]))
		
	print(positions)
	return mds
	
print(readMetadata())