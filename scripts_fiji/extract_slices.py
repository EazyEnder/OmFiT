"""
Fiji script: Extract slices from group of stacks
"""

import os  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver

#dict: "parent_folder"->"field with colony nbr"->list of slice index
#TO_EXTRACT = {
#"/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/":
#{"wt5_3":[66,76,77,86],"wt5_1":[72,73,89,91],"wt5_2":[72,77,82,85],"wt5_8":[26,32,34,87],"wt3_2":[49,77,152,163],"wt3_11":[34,87,153,166]},
#"/media/irina/5C00325A00323B7A/Zack/data/nice_ss30-25_nov20-22_2023/":
#{"dt2_1":[8,31,41,162],"wt0_1":[154,165,5,46]}
#}

TO_EXTRACT = {
"/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/":
{"wt5_5":[45,57,128,79],"wt5_6":[53,80,112,127],"wt5_7":[47,56,75,130],"wt5_13":[77,82,87,93],"wt5_9":[49,83,127,136],"wt5_10":[73,82,87,93],"wt5_11":[46,67,71,136],"wt5_12":[72,77,92,35]},
}

EXPORT_DIR = "/media/irina/5C00325A00323B7A/Zack/data/needmasks/"

SUFFIX = "_phase"

def main():
	for p_folder in TO_EXTRACT.keys():
		for dataset in TO_EXTRACT[p_folder].keys():
			print("work on "+dataset)
			directory = os.path.join(p_folder,dataset.split("_")[0])
			if not(os.path.exists(directory)):
				print("no folder -> abort "+dataset)
				continue
				
			imp = IJ.openVirtual(os.path.join(directory, dataset+SUFFIX+".tif"))
			stack = imp.getImageStack()
			for slice_i in TO_EXTRACT[p_folder][dataset]:
				ip = stack.getProcessor(slice_i)
				#fs = FileSaver(ip)
				fs = FileSaver(ImagePlus(directory+"_"+str(slice_i), ip))
				fs.saveAsTiff(os.path.join(EXPORT_DIR,dataset+"_"+str(slice_i)+".tif"))
			print(dataset + " saved")
				
main()