"""
Fiji script: Extract raw slices and corresponding masks from trackmate xml file
"""

from fiji.plugin.trackmate.io import TmXmlReader
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate import TrackMate
from java.io import File
import sys
import os  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from fiji.plugin.trackmate.action import LabelImgExporter


TO_EXTRACT = {
"/media/irina/5C00325A00323B7A/Zack/data/nice_ss30_nov13-20_2023/":
{"wt5_1":[96,51,79,40],"wt5_2":[138,70,121,94],"wt5_3":[79,104,138,94],"wt5_4":[107,138,70,44],"wt5_5":[104,116,50,18],"wt5_6":[94,108,129,137],"wt5_7":[30,58,95,108],"wt5_8":[85,114,138,100],"wt5_9":[50,97,120,35],"wt5_10":[97,127,138,83]},
}

EXPORT_DIR = "/media/irina/5C00325A00323B7A/Zack/ogm/"
SUFFIX = "_phase"

reload(sys)
sys.setdefaultencoding('utf-8')

def main():
	for p_folder in TO_EXTRACT.keys():
			for dataset in TO_EXTRACT[p_folder].keys():
				dset_concatenate = dataset.replace("_","")
				print("work on "+dataset)
				directory = os.path.join(p_folder,dataset.split("_")[0])
				if not(os.path.exists(directory)):
					print("no folder -> abort "+dataset)
					continue
					
				#Saving raws
				imp = IJ.openVirtual(os.path.join(directory, dataset+SUFFIX+".tif"))
				stack = imp.getImageStack()
				for slice_i in TO_EXTRACT[p_folder][dataset]:
					ip = stack.getProcessor(slice_i)
					fs = FileSaver(ImagePlus(directory+"_"+str(slice_i), ip))
					fs.saveAsTiff(os.path.join(EXPORT_DIR,dset_concatenate+"_"+str(slice_i)+".tif"))
				print(dataset + " raws saved")
				
				xml_file = File(os.path.join(directory, dataset+SUFFIX+".xml"))
				logger = Logger.IJ_LOGGER
				
				reader = TmXmlReader(xml_file)
				if not reader.isReadingOk():
				    sys.exit(reader.getErrorMessage())
				    
				model = reader.getModel()
				imp = reader.readImage()
				imp_dims = imp.getDimensions()
				imp.setDimensions(imp_dims[2], imp_dims[4], imp_dims[3]) 
				settings = reader.readSettings( imp )
				trackmate = TrackMate(model, settings)
				imp_mask = LabelImgExporter.createLabelImagePlus(trackmate,False,False,LabelImgExporter.LabelIdPainting.LABEL_IS_INDEX)
				stack = imp_mask.getImageStack()
				for slice_i in TO_EXTRACT[p_folder][dataset]:
					ip = stack.getProcessor(slice_i)
					fs = FileSaver(ImagePlus(directory+"_"+str(slice_i), ip))
					fs.saveAsTiff(os.path.join(EXPORT_DIR,dset_concatenate+"_"+str(slice_i)+"_mask"+".tif"))
				print(dataset + " masks saved")
				

main()