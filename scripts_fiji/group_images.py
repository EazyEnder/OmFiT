import os, sys  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from ij.plugin import Scaler, StackCombiner
from math import floor
from ij.gui import Roi
from java.awt import Rectangle
  
sourceDir = "/home/irina/Documents/train_need_prepro/masks/"
targetDir = "/home/irina/Documents/train_need_prepro/outputs/"

IS_MASKS = True
ITERATION = 1

def containsDataSet(datasets,name):
	for i,dataset in enumerate(datasets):
		if(len(dataset) < 1):
			print("Error: a dataset is empty but initialized")
			return
		if(dataset[0].split("_")[0] == name):
			return i
	return -1

def process(f11,f12,f21,f22):
	#Scale
	if(f11.width*f11.height!=f12.width*f12.height or f21.width*f21.height!=f22.width*f22.height):
		print("Error: img dimension is not constant in a dataset")
		return
	
	sf11 = f11
	sf12 = f12
	sf21 = f21
	sf22 = f22
	if(f11.width < f21.width):
		sf11 = f21
		sf12 = f22
		sf21 = f11
		sf22 = f12
		
	RAT = 1.*sf21.width/sf11.width
	bf11 = sf11.duplicate()
	bf12 = sf12.duplicate()
	sf11 = Scaler.resize(sf11, int(sf11.width*RAT), int(sf11.height*RAT), 1, "none")
	sf12 = Scaler.resize(sf12, int(sf12.width*RAT), int(sf12.height*RAT), 1, "none")
		
	if IS_MASKS:
		toprocess = [sf11,sf12,sf21,sf22]
		before = [bf11,bf12,sf21.duplicate(),sf22.duplicate()]
		offset_index = 0
		for i,mask in enumerate(toprocess):
			mp = mask.getProcessor()
			bp = before[i].getProcessor()
			maximum = offset_index
			for x in range((mask.width)):
				for y in range((mask.height)):
					b_px_val = 0
					npxs_val = [0,0,0,0]
					if i < 2:
						b_px_val=bp.getValue(int((x/RAT)),int((y/RAT)))
						npxs_val = [bp.getValue(int((x/RAT)),int((y/RAT))-1),bp.getValue(int((x/RAT)),int((y/RAT))+1),bp.getValue(int((x/RAT))-1,int((y/RAT))),bp.getValue(int((x/RAT))+1,int((y/RAT)))]
					else:
						b_px_val=bp.getValue(x,y)
						npxs_val = [bp.getValue(x,y-1),bp.getValue(x,y+1),bp.getValue(x-1,y),bp.getValue(x+1,y)]
						
					if b_px_val == 0:
						if npxs_val[0] != 0 and npxs_val[0]==npxs_val[1] and npxs_val[1]==npxs_val[2] and npxs_val[2]==npxs_val[3]:
							print("Pixel modified m:"+str(i+1)+" (x:"+str(x)+" ,y:"+str(y)+"): "+str(offset_index+npxs_val[0]))
							b_px_val=npxs_val[0]
						else:
							mp.putPixel(x,y,0)
							continue
					maximum = max(maximum,b_px_val)
					mp.putPixel(x,y,int(offset_index+b_px_val))
			offset_index = maximum
	
	#Combine
	scombiner = StackCombiner()
	is_left = scombiner.combineVertically(ImageStack.create([sf11]),ImageStack.create([sf22]))
	is_right = scombiner.combineVertically(ImageStack.create([sf21]),ImageStack.create([sf12]))
	
	ip = ImagePlus("gray", scombiner.combineHorizontally(is_left, is_right))
	
	#Save
	global ITERATION
	
	fs = FileSaver(ip)
	name = targetDir+str(ITERATION)
	if IS_MASKS:
		name += "_mask"
	fs.saveAsTiff(name+".tif")
	
	print("Success for " + str(ITERATION))
	ITERATION += 1
	
def cropImg(img,name,crops):
	if(len(crops) == 0):
		return img
	time = int(name.split("_")[1])
	crop_path = ""
	for c in crops:
		if c.split("_")[0] == name.split("_")[0]:
			crop_path = c
	crop_file = open(os.path.join(sourceDir,crop_path), "r")
	
	x0 = 0
	y0 = 0
	x1 = img.width
	y1 = img.height
	for i,line in enumerate(crop_file):
		if(i == time-1):
			coo = line.split(",")
			x0 = float(coo[0])
			y0 = float(coo[1])
			x1 = float(coo[2])
			y1 = float(coo[3])
			break
	ip = img.getProcessor()
	ip.setRoi(int(x0),int(y0),int(x1-x0),int(y1-y0));
	return ImagePlus("cropped_img",ip.crop())
	

#Create groups
def group(dataset1, dataset2, crops):
	imgs1 = []
	imgs2 = []
	#Open imgs
	for f in dataset1:
		im = IJ.openImage(os.path.join(sourceDir, f))
		imgs1.append(cropImg(im, f,crops))
	for f in dataset2:
		im = IJ.openImage(os.path.join(sourceDir, f))
		imgs2.append(cropImg(im, f,crops))
		
	max_groups = int(floor(min(len(imgs1)-len(imgs1)%2,len(imgs2)-len(imgs2)%2)/2))
	print("Max Groups possible in this pair: "+str(max_groups))
	
	for i in range(max_groups):
		f11 = imgs1[i]
		f12 = imgs1[-(i+1)]
		f21 = imgs2[i]
		f22 = imgs2[-(i+1)]
		process(f11,f12,f21,f22)

def main(folder):
	datasets = []
	crops = []
	#Get files
	for filename in os.listdir(folder):
		dset = filename.split("_")[0]
		if(filename.split("_")[1] == "crop" or filename.split("_")[1] == "crop.txt"):
			if(not(filename in crops)):
				crops.append(filename)
			continue
		dset_index = containsDataSet(datasets,dset)
		if(dset_index is None):
			return
		if(dset_index <= -1):
			datasets.append([filename])
		else:
			datasets[dset_index].append(filename)
	#Sort files 
	sorted_datasets = []
	for dataset in datasets:
		N = []
		for dset in dataset:
			N.append(int(dset.split("_")[1]))
		N.sort()
		sorted_dset = []
		for i,n in enumerate(N):
			if IS_MASKS:
				sorted_dset.append(dset.split("_")[0]+"_"+str(n)+"_mask_.tif")
			else:
				sorted_dset.append(dset.split("_")[0]+"_"+str(n)+"_.tif")
		sorted_datasets.append(sorted_dset)
	datasets = sorted_datasets
	
	LEN_DATASETS = len(datasets)
	if(LEN_DATASETS % 2 != 0):
		print("can't pair one dataset -> ignored")
	
	print("Number of DS: "+str(LEN_DATASETS))
	#Group pairs of datasets
	i = 0
	while i < LEN_DATASETS and i+1 < LEN_DATASETS:
		group(datasets[i],datasets[i+1],crops)
		i += 2
		
main(sourceDir)

	    
	    
    
