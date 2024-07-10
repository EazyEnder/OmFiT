"""
Fiji script: Apply registration 
"""

#Field
POSITION = "wt2"
#Path to the files
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/nov20/"+POSITION+"/"
#Files that we will use / Color names
COLORS_FILE = ["phase_cropped", "y_cropped", "r_cropped"]
#COLORS_FILE = ["phase_cropped", "y_cropped", "r_cropped"]

#Colors channels order
COLORS = ["gray", "yellow", "red"]

#If there is already a file with the channels merged, we'll use it (if REWRITE==False)
REWRITE = False


#-----------------------------------------------------
import os
from ij import IJ, ImagePlus
from ij.io import FileSaver
from ij.plugin import RGBStackMerge
from plugin import Descriptor_based_series_registration
from java.lang.reflect import Array

def mergeChannels(channels_stacks, names):
	print("Merging channels :" + str(names))
	hexColors = ["#ff0000", "#00ff00","#0000ff","#ffffff", "#00ffff", "#ff00ff", "#ffff00"]
	colorNames = ["red", "green", "blue", "gray", "cyan", "magenta", "yellow"]
	images = Array.newInstance(ImagePlus,len(colorNames))
	for color,name in zip(COLORS,names):
	    channelIndex = hexColors.index(color.lower()) if color[0] == "#" else colorNames.index(color.lower())
	    images[channelIndex] = channels_stacks[names.index(name)]
	merged = RGBStackMerge.mergeChannels(images, False)
	print("Channels merged")
	print("Saving the image")
	fs = FileSaver(merged)
	fs.saveAsTiff(os.path.join(DIR_PATH,"channelsMerged.tif"));
	print("Image saved")
	return True

def main():
	channels_stacks = []
	names = []
	already_exist = False 
	for f,file_name in enumerate(os.listdir(DIR_PATH)):
		if len(file_name.split(".")) <= 1:
			continue
		if file_name.split(".")[0] == "channelsMerged":
			already_exist = True
		if file_name.split(".")[1] in ["tif","tiff"] and file_name.split(".")[0] in COLORS_FILE:
			channels_stacks.append(IJ.openVirtual(os.path.join(DIR_PATH,file_name)))
			names.append(file_name.split(".")[0])
	if (already_exist and not(REWRITE)):
		print("File already exists -> using it")
	if (already_exist and not(REWRITE)) or mergeChannels(channels_stacks,names):
		imp = IJ.openVirtual(os.path.join(DIR_PATH,"channelsMerged.tif"))
		imp.show()
		desc = Descriptor_based_series_registration()
		desc.run("")
	
main()