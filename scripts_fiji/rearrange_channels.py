"""
Fiji script: Rearrange channels
"""

# 1st: phase, 2nd: fluo yellow, 3th: fluo red
NEW_ORDER = [2,1,3]

#Pos can be a list of positions -> the script will modify a list of folders.
POSITION = "wt4"
#POSITION = ["wt0","wt1","wt2","wt3","dt0","dt1","dt2","dt3"]

#Path to the files
DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/feb12/"

#Name of the tiff file that will be used
TIFF_NAME="registered"

#-------------------------------------------
import os  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from ij.plugin import ChannelArranger

def main(position):
	dir_path = DIR_PATH + position + "/"
	if not(os.path.exists(dir_path)):
		print(dir_path+" does not exist")
		return
	print("Begin work on "+position)
	for f,file_name in enumerate(os.listdir(dir_path)):
		if not(file_name.split(".")[1] in ["tif","tiff"]) or not(TIFF_NAME == file_name.split(".")[0]):
			continue
		img = IJ.openVirtual(os.path.join(dir_path,file_name))
		img2 = ChannelArranger.run(img, NEW_ORDER)
		#img2.setDisplayMode(IJ.COLOR)
		print("Saving "+position)
		fs = FileSaver(img2)
		fs.saveAsTiff(os.path.join(dir_path,file_name.split(".")[0]+"_arranged.tif"))
		print(position+" saved")
	
if type(POSITION) is list:
	for pos in POSITION:
		main(pos)
else:
	main(POSITION)