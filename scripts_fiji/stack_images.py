"""
Fiji script: Concatenate all the stacks/imgs together

Settings:
"""

#Field(s)
POSITIONS = ["dt0","dt1","dt2","dt3","dt4","wt0","wt1","wt2","wt3"]
#Export path
EXPORT_PATHS = ["/media/irina/5C00325A00323B7A/Zack/feb12/"+POS+"/" for POS in POSITIONS]

#list of path in order. The program will take field files from all the src paths. 
SRC_PATH = ["/media/irina/LIPhy-INFO/cyano/feb12/ini_25_"]
#Color names
COLORS = ["phase", "y", "r"]
#MicroManager channel number, in the same order of COLORS
MM_NAME= ["000" ,"001" ,"002"]
#Minimum index for all src path
IDX_FILE_BEGIN = 1
#Maximum index for all src path. If there is no folder corresponding to the index -> just put an empty list.
IDX_FILE_END = 12

#------------------------------------------------------

import os, sys
from ij import IJ, ImagePlus, ImageStack  
from ij.plugin import Concatenator
from ij.io import FileSaver
import json
import gc

from datetime import datetime

#file_time = os.path.getmtime("")

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def main(POSITION,EXPORT_PATH):

	RESULT = {}
	for i in range(len(COLORS)):
		print("Working on "+COLORS[i])
		RESULT[COLORS[i]] = {}
		channel_name = MM_NAME[i]
		channel_color = MM_NAME[i]
		rslt_imp = None
		
		T_BEGIN = None
		GLOBAL_IMG_INDEX = 0
		LAST_INDEX = IDX_FILE_BEGIN-1
		for src in range(len(SRC_PATH)):
			print("Files from "+ SRC_PATH[src])
			for j in range(IDX_FILE_BEGIN, IDX_FILE_END+1):
				LAST_INDEX += 1
				print("Sub work on "+str(LAST_INDEX))
				if(not(os.path.exists(SRC_PATH[src]+str(j)+"/"+POSITION+"/"))):
					continue
				RESULT[COLORS[i]][LAST_INDEX] = {
				"times": []
				}
				files = []
				unsorted_times = []	
				for f,filename in enumerate(os.listdir(SRC_PATH[src]+str(j)+"/"+POSITION+"/")):
					if not("channel"+MM_NAME[i] in filename.split("/")[-1]):
						continue
					files.append(filename)
					unsorted_times.append(os.path.getmtime(os.path.join(SRC_PATH[src]+str(j)+"/"+POSITION+"/",filename)))
				imgs = []
				times = []
				delta_times = []
				for f in argsort(unsorted_times):	
					imgs.append(IJ.openVirtual(os.path.join(SRC_PATH[src]+str(j)+"/"+POSITION+"/",files[f])))
					times.append(unsorted_times[f])
					if T_BEGIN is None:
						T_BEGIN = times[f]
					delta_times.append(times[-1]-T_BEGIN)
				if len(imgs) < 1:
					continue
				stack = ImageStack(imgs[0].width, imgs[0].height)
				gii = []
				for img in imgs:
					stack.addSlice(img.getProcessor())
					gii.append(GLOBAL_IMG_INDEX)
					GLOBAL_IMG_INDEX += 1
				
				RESULT[COLORS[i]][LAST_INDEX]["times"] = times
				RESULT[COLORS[i]][LAST_INDEX]["delta_t"] = delta_times
				RESULT[COLORS[i]][LAST_INDEX]["global_index"] = gii
				real_times = []
				for t in times:
					real_times.append(datetime.fromtimestamp(t).strftime("%m/%d/%Y, %H:%M:%S"))
				RESULT[COLORS[i]][j]["dates"] = real_times
				
				paths = []
				for t in range(len(times)):
					paths.append(os.path.join((SRC_PATH[src]+str(j)).split("/")[-1]+"/"+POSITION+"/",files[t]))
				RESULT[COLORS[i]][j]["paths"] = paths
				
				imp = ImagePlus("composite", stack)
				
				if(rslt_imp is None):
					rslt_imp = imp
					continue
				rslt_imp = Concatenator.run(rslt_imp,imp)
		print("Saving "+COLORS[i])
		fs = FileSaver(rslt_imp)
		fs.saveAsTiff(EXPORT_PATH+COLORS[i]+".tif")
		
		del rslt_imp
		del fs
		gc.collect()
			
	with open(EXPORT_PATH+"result.json", "w") as outfile:
		json.dump(RESULT, outfile, indent=2)
	print("End")

for i in range(len(POSITIONS)):
	print("Work on: "+ POSITIONS[i])
	main(POSITIONS[i],EXPORT_PATHS[i])