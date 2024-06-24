"""
Fiji script: Crop & Follow through time a part of a stack 
"""

#Field
POSITION = "wt3"
#Path to the files
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/"+POSITION+"/"

#Divide the movie into time intervals, the end of a time interval is before a huge move
TIMES = [(0,97),(98,-1)]
#REGIONS is a list of:
#[(POSITION X & Y),(SIZE WIDTH & HEIGHT)]
REGIONS = [[(1469,1163),(579,579)],[(1052,473),(579,579)]] #wt2 transi

#Channels name
CHANNELS = ["phase", "y", "r"]

#--------------------------------------------

import os  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver

def crop(imp):
	stack = imp.getImageStack()
	new_stack = ImageStack(REGIONS[0][1][0], REGIONS[0][1][1])
	for i in range(imp.getNSlices()):
		time_index = -1
		for j,time_int in enumerate(TIMES):
			if (time_int[0] < 0 or i+1 >= time_int[0]) and (i+1 <= time_int[1] or time_int[1] < 0):
				time_index = j
				break
		if time_index == -1:
			print("Warning: No time interval for frame:"+str(i+1))
		ip = stack.getProcessor(i+1)
		ip.setRoi(int(REGIONS[j][0][0]),int(REGIONS[j][0][1]),int(REGIONS[j][1][0]),int(REGIONS[j][1][1]));
		new_stack.addSlice(ip.crop())
	return new_stack
	
def main():
	for f,file_name in enumerate(os.listdir(DIR_PATH)):
		if file_name.split(".")[1] in ["tif","tiff"] and file_name.split(".")[0] in CHANNELS:
			print("Cropping: "+file_name)
			cropped_stack = crop(IJ.openVirtual(os.path.join(DIR_PATH,file_name)))
			fs = FileSaver(ImagePlus("cropped_stack", cropped_stack))
			fs.saveAsTiff(os.path.join(DIR_PATH,file_name.split(".")[0]+"_cropped.tif"))
			print("Stack " + file_name + " modified")

main()