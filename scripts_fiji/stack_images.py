"""
Fiji script: Concatenate all the stacks/imgs together
"""

import os, sys
from ij import IJ, ImagePlus, ImageStack  
from ij.plugin import Concatenator
from ij.io import FileSaver
import json

from datetime import datetime

#concatenate all the imgs

POSITION = "wt4"
EXPORT_PATH = "/media/irina/LIPhy-INFO/test/nice_ss30_nov13-20_2023/"+POSITION+"/"
SRC_PATH = "/media/irina/LIPhy-INFO/cyano/nov13_nice_ss30/steady_state30_"
COLORS = ["phase", "y", "r"]
MM_NAME= ["000" ,"001" ,"002"]
IDX_FILE_BEGIN = 1
IDX_FILE_END = 12

#file_time = os.path.getmtime("")

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def main():

	RESULT = {}
	for i in range(len(COLORS)):
		print("Working on "+COLORS[i])
		RESULT[COLORS[i]] = {}
		channel_name = MM_NAME[i]
		channel_color = MM_NAME[i]
		rslt_imp = None
		
		T_BEGIN = None
		GLOBAL_IMG_INDEX = 0
		for j in range(IDX_FILE_BEGIN, IDX_FILE_END+1):
			print("Sub work on "+str(j))
			if(not(os.path.exists(SRC_PATH+str(j)+"/"+POSITION+"/"))):
				continue
			RESULT[COLORS[i]][j] = {
			"times": []
			}
			files = []
			unsorted_times = []	
			for f,filename in enumerate(os.listdir(SRC_PATH+str(j)+"/"+POSITION+"/")):
				if not("channel"+MM_NAME[i] in filename.split("/")[-1]):
					continue
				files.append(filename)
				unsorted_times.append(os.path.getmtime(os.path.join(SRC_PATH+str(j)+"/"+POSITION+"/",filename)))
			imgs = []
			times = []
			delta_times = []
			for f in argsort(unsorted_times):	
				imgs.append(IJ.openImage(os.path.join(SRC_PATH+str(j)+"/"+POSITION+"/",files[f])))
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
			
			RESULT[COLORS[i]][j]["times"] = times
			RESULT[COLORS[i]][j]["delta_t"] = delta_times
			RESULT[COLORS[i]][j]["global_index"] = gii
			#if you want the dates -> not json serializable
			#real_times = []
			#for t in times:
			#	real_times.append(datetime.fromtimestamp(t))
			#RESULT[COLORS[i]][j]["times"] = real_times
			imp = ImagePlus("composite", stack)
			
			if(rslt_imp is None):
				rslt_imp = imp
				continue
			rslt_imp = Concatenator.run(rslt_imp,imp)
		print("Saving "+COLORS[i])
		fs = FileSaver(rslt_imp)
		fs.saveAsTiff(EXPORT_PATH+COLORS[i]+".tif")
		rslt_imp = None
			
	with open(EXPORT_PATH+"result.json", "w") as outfile:
		json.dump(RESULT, outfile)
		
main()