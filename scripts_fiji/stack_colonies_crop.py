"""
Fiji script: Crop and divide each colony in a stack (using crop's csv file)
"""

import os  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver

POSITION = "wt1"
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/"+POSITION+"/"
FILE_NAME = "registered_arranged"
CHANNEL_NAME = ["phase","y","r"]

ROI_CSV_OFFSET = 2

JUST_DIVIDE_CHANNELS = False

import csv
def getCropsROIs():
	if JUST_DIVIDE_CHANNELS:
		return
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

def crop(imp,file_name):

	global CROPS
	if not(JUST_DIVIDE_CHANNELS) and (CROPS is None or len(CROPS) < 1):
		print("CROPS has no elements or is null")
		return
	print("Begin cropping")
	stack = imp.getImageStack()
	if JUST_DIVIDE_CHANNELS:
		CROPS = []
		CROPS.append([(0,0),(imp.width,imp.height)])
	for c,crop in enumerate(CROPS):
		print("Cropping area "+str(c+1)+"/"+str(len(CROPS)))
		i = 0
		for j,name in enumerate(CHANNEL_NAME):
			new_stack = ImageStack(crop[1][0], crop[1][1])
			for i in range(0,stack.getSize(),3):
				ip = stack.getProcessor(j+i+1)
				ip.setRoi(int(crop[0][0]),int(crop[0][1]),int(crop[1][0]),int(crop[1][1]));
				new_stack.addSlice(ip.crop())
			fs = FileSaver(ImagePlus("cropped_stack_"+name+"_"+str(c), new_stack))
			fs.saveAsTiff(os.path.join(DIR_PATH,POSITION+"_"+str(c+1)+"_"+name+".tif"))
		print("Area"+str(c+1)+"/"+str(len(CROPS))+" saved")
	
def main():
	for f,file_name in enumerate(os.listdir(DIR_PATH)):
		if file_name.split(".")[1] in ["tif","tiff"] and file_name.split(".")[0] == FILE_NAME:
			print("Cropping: "+file_name)
			crop(IJ.openVirtual(os.path.join(DIR_PATH,file_name)),file_name)
			print("Stack " + file_name + " fully cropped")

main()
			