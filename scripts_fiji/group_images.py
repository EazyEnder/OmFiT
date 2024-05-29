import os, sys  
from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from ij.plugin import Scaler, StackCombiner
  
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
		
	if IS_MASKS:
		toprocess = [sf11,sf12,sf21,sf22]
		offset_index = 0
		for i,mask in enumerate(toprocess):
			mp = mask.getProcessor()
			pixels = mp.getPixels()
			maximum = 0
			for x in range((mask.width)):
				for y in range((mask.height)):
					px_val = mp.getValue(x,y)
					if(px_val == 0):
						continue
					maximum = max(maximum,px_val)
					mp.putPixel(x,y,int(offset_index+px_val))
			offset_index += maximum
		
		
	RAT = 1.*sf21.width/sf11.width
	sf11 = Scaler.resize(sf11, int(sf11.width*RAT), int(sf11.height*RAT), 1, "none")
	sf12 = Scaler.resize(sf12, int(sf12.width*RAT), int(sf12.height*RAT), 1, "none")
	
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
	
	ITERATION += 1
	print("Success for " + str(ITERATION))
		

#Create groups
def group(dataset1, dataset2):
	imgs1 = []
	imgs2 = []
	#Open imgs
	for f in dataset1:
		imgs1.append(IJ.openImage(os.path.join(sourceDir, f)))
	for f in dataset2:
		imgs2.append(IJ.openImage(os.path.join(sourceDir, f)))
		

	max_groups = min(len(imgs1)-len(imgs1)%2,len(imgs2)-len(imgs2)%2)
	print("Max Groups possible in this pair: "+str(max_groups))
	
	for i in range(max_groups):
		f11 = imgs1[i]
		f12 = imgs1[-(i+1)]
		f21 = imgs2[i]
		f22 = imgs2[-(i+1)]
		process(f11,f12,f21,f22)

def main(folder):
	datasets = []
	#Get files
	for filename in os.listdir(folder):
		dset = filename.split("_")[0]
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
		group(datasets[i],datasets[i+1])
		i += 2
		
main(sourceDir)

	    
	    
    
