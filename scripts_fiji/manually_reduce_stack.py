"""
Fiji script: Manually reduce stack using index intervals
First use stack_images.py
Then you can use this script on the export dir
"""

#!!! the DIR NEED to contains only the channels stacks and a json file giving times. No more

#Field
POSITION = "wt0"
#Path to the files
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/feb12/"+POSITION+"/"

#For example (2,10) gives [2,10] so all indexes between 2 and 10 will be removed, i.e 2 <= i <= 10

INTERVALS_TO_REMOVE = [(0,29),(35,36),(51,83),(132,132),(134,134),(136,-1)]
#Just modify the json file, not the .tiff
ONLY_JSON = False
#Just modify the file which have the ONLY_STRING (string var) in his name
ONLY_STRING = None

#------------------------------------------------------------------

import os
import json
from ij.io import FileSaver
from ij import IJ, ImagePlus, ImageStack  
import copy


STATIC_DATA = None

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

def isInInterval(index):
	for i in INTERVALS_TO_REMOVE:
		if  index >= i[0]:
			if i[1] == -1 or index <= i[1]:
				return True
	return False

def modifyJson(file_name):
	f = open(os.path.join(DIR_PATH,file_name))
	data = json.load(f)
	global STATIC_DATA
	STATIC_DATA = copy.deepcopy(data)
	
	for channel in data.keys():
		global_idx_offset = 0
		sorted_keys_indexes = argsort([int(nbr) for nbr in (data[channel].keys())])
		for index in [data[channel].keys()[ski] for ski in sorted_keys_indexes]:
	 		gii = data[channel][index]["global_index"]
	 		if "old_index" in data[channel][index].keys():
	 			gii = data[channel][index]["old_index"]
	 		index_to_keep = []
	 		for i in range(len(gii)):
	 			if isInInterval(gii[i]+1):
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
	with open(os.path.join(DIR_PATH,file_name), "w") as outfile:
		json.dump(data, outfile, indent=2)
	print("JSON " + file_name + " modified")
	
def getFrameIndex(global_index):

	data = STATIC_DATA
	if data is None:
		f_json = None
		for f in os.listdir(DIR_PATH):
			if f.split(".")[1] in ["json"]:
				f_json = f
		f = open(os.path.join(DIR_PATH,f_json))
		data = json.load(f)
		f.close()
	
	for channel in data.keys():
		global_idx_offset = 0
		for index in data[channel].keys():
	 		gii = data[channel][index]["global_index"]
	 		cii = data[channel][index]["global_index"]
	 		if "old_index" in data[channel][index].keys():
	 			gii = data[channel][index]["old_index"]
	 		for i in range(len(gii)):
	 			if cii[i] == global_index:
	 				return gii[i]
	 
	print("Error in using json information ")
	return None

def modifyStack(file_name):
	channel = file_name.split(".")[0]
	imp = IJ.openVirtual(os.path.join(DIR_PATH,file_name))
	stack = imp.getImageStack()
	
	new_stack = ImageStack(imp.width, imp.height)
	for i in range(imp.getNSlices()):
		if isInInterval(getFrameIndex(i)+1):
			continue
		new_stack.addSlice(None, stack.getProcessor(i+1)) 
	imp = ImagePlus("filtered_stack", new_stack)
	fs = FileSaver(imp)
	fs.saveAsTiff(os.path.join(DIR_PATH,file_name))
	print("Stack " + file_name + " modified")
	imp = None

def main():
	if ONLY_JSON:
		print("Only change json file")
	if not(ONLY_STRING is None):
		print("Only filename containing: "+ONLY_STRING)
	for f,file_name in enumerate(os.listdir(DIR_PATH)):
		if not(ONLY_STRING is None) and not(ONLY_STRING in file_name):
			continue
		if file_name.split(".")[1] in ["tif","tiff"] and not(ONLY_JSON):
			modifyStack(file_name)
			continue
		if file_name.split(".")[1] in ["json"]:
			modifyJson(file_name)
			continue
main()
print("end")

