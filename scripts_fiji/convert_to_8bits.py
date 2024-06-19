import os
from ij import IJ
from ij.process import ImageConverter


DIR_PATH = "/media/irina/5C00325A00323B7A/Zack/ogm/"

for filename in os.listdir(DIR_PATH):
	imp = IJ.openImage(os.path.join(DIR_PATH,filename));
	IJ.run(imp, "Enhance Contrast", "saturated=0.35");
	ImageConverter.setDoScaling(True);
	IJ.run(imp, "8-bit", "");
	IJ.run(imp, "Save", "");
	imp.close();
