"""
Fiji script: Update stack following the history between the stack's json & the newest/updated json
"""

COLONY_NAME = "wt3c10"

OLD_JSON_PATH = "/media/irina/5C00325A00323B7A/Zack/data/export/time/"+COLONY_NAME.split("c")[0]+".json"
NEW_JSON_PATH = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME+"/"+COLONY_NAME+".json"

OLD_TIFF = "/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/"+COLONY_NAME.split("c")[0].replace("T","")+"/"+COLONY_NAME.replace("c","_").replace("T","")+"_r.tif"
EXPORT_DIR = "/media/irina/5C00325A00323B7A/Zack/data/export/"+COLONY_NAME

#-----------------------------------------------------------------------------------

import os, json
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver

f = open(OLD_JSON_PATH)
old_data = json.load(f)
f.close()
f = open(NEW_JSON_PATH)
new_data = json.load(f)
f.close()

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

slices_to_remove = []
channel = old_data.keys()[0]
for index in old_data[channel].keys():
	new_oii = new_data[channel][index]["old_index"]
	old_gii = old_data[channel][index]["global_index"]
	for i,oii in enumerate(old_data[channel][index]["old_index"]):
		if not(oii in new_oii):
			slices_to_remove.append(old_gii[i])

if len(slices_to_remove) != 0:
	slices_to_remove = [slices_to_remove[i] for i in argsort(slices_to_remove)]

old_name = OLD_TIFF.split("/")[-1].replace("c","_")
imp = IJ.openImage(os.path.join(OLD_TIFF.split(OLD_TIFF.split("/")[-1])[0],old_name))
imp_name = OLD_TIFF.split("/")[-1]

ist = imp.getImageStack()
for i in range(len(slices_to_remove)):
	sli = slices_to_remove[len(slices_to_remove)-1-i]
	ist.deleteSlice(sli+1)
imp = ImagePlus("",ist)

fs = FileSaver(imp)
fs.saveAsTiff(os.path.join(EXPORT_DIR,imp_name))
print("Saved")

