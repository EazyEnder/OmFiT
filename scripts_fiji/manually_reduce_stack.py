"""
Fiji script: Manually reduce stack using index intervals
First use stack_images.py
Then you can use this script on the export dir
"""

import os
import json
from ij.io import FileSaver
from ij import IJ, ImagePlus, ImageStack  
import copy

#the dir contains only the channels stacks and a json file giving times

POSITION = "wt4"
DIR_PATH = "/media/irina/LIPhy-INFO/test/nice_ss30_nov13-20_2023/"+POSITION+"/"
INTERVALS_TO_REMOVE = [(200,-1),(96,99),(141,145), (41,42)] #WT4
#INTERVALS_TO_REMOVE = [(42,42),(92,95),(97,98),(143,146),(149,150),(181,186),(200,-1)] #WT3
#INTERVALS_TO_REMOVE = [(42,42),(89,89),(97,98),(143,144),(147,148),(185,185),(200,-1)] #WT5
ONLY_JSON = False

def isInInterval(index):
	for i in INTERVALS_TO_REMOVE:
		if  index >= i[0]:
			if i[1] == -1 or index <= i[1]:
				return True
	return False

def modifyJson(file_name):
	f = open(os.path.join(DIR_PATH,file_name))
	data = json.load(f)
	
	for channel in data.keys():
		global_idx_offset = 0
		for index in data[channel].keys():
	 		gii = data[channel][index]["global_index"]
	 		index_to_keep = []
	 		for i in range(len(gii)):
	 			if isInInterval(gii[i]+1):
	 				continue
	 			index_to_keep.append(i)
	 		for k in data[channel][index].keys():
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
		json.dump(data, outfile)
	print("JSON " + file_name + " modified")

def modifyStack(file_name):
	channel = file_name.split(".")[0]
	imp = IJ.openVirtual(os.path.join(DIR_PATH,file_name))
	stack = imp.getImageStack()
	
	new_stack = ImageStack(imp.width, imp.height)
	for i in range(imp.getNSlices()):
		if isInInterval(i+1):
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
	for f,file_name in enumerate(os.listdir(DIR_PATH)):
		if file_name.split(".")[1] in ["tif","tiff"] and not(ONLY_JSON):
			modifyStack(file_name)
			continue
		if file_name.split(".")[1] in ["json"]:
			modifyJson(file_name)
			continue
main()

