import numpy as np
from pathlib import Path
import os
from cellpose_omni import io, utils, models, core
import omnipose
from track_objects import Clip
from utils import  serializeMasks
from plot import plotTracking
import time
from GlobalStorage import setRUN, getRUN

OMNI_DIR = Path(omnipose.__file__).parent.parent
BASE_DIR = os.path.join(OMNI_DIR,'data')
USE_GPU = core.use_gpu()

class OmniposeRun():

    def __init__(self,saveMasks:bool=False,saveOutlines:bool=False):
        self.model_name = "bact_phase_omni"
        self.model = models.CellposeModel(gpu=USE_GPU, model_type=self.model_name)
        self.chans = [0,0]
        self.saveMasks = saveMasks
        self.saveOutlines = saveOutlines
        self.saveOmniposeFiles = False
        self.basedir = BASE_DIR

        self.params = {'channels':self.chans, # always define this with the model
                'rescale': None, # upscale or downscale your images, None = no rescaling 
                'mask_threshold': -1, # erode or dilate masks with higher or lower values 
                'flow_threshold': 0., # default is .4, but only needed if there are spurious masks to clean up; slows down output
                'transparency': True, # transparency in flow output
                'omni': True, # we can turn off Omnipose mask reconstruction, not advised 
                'cluster': True, # use DBSCAN clustering
                'resample': True, # whether or not to run dynamics on rescaled grid or original grid 
                'verbose': False, # turn on if you want to see more output 
                'tile': False, # average the outputs from flipped (augmented) images; slower, usually not needed 
                'niter': None, # None lets Omnipose calculate # of Euler iterations (usually <20) but you can tune it for over/under segmentation 
                'augment': False, # Can optionally rotate the image and average outputs, usually not needed 
                'affinity_seg': False, # new feature, stay tuned...
                }

    def run(self):

        files = np.array([str(p) for p in Path(self.basedir).glob("*c1.tif")])
        t_index = []
        for f in files:
            t = int(f.split(".")[0].split("t")[-1].split("xy")[0])
            t_index.append(t)
        files = files[np.argsort(t_index)]
        files = files[::1]
        self.files = files
        self.imgs = [io.imread(f) for f in files]

        tic = time.time() 
        self.masks, self.flows, self.styles = self.model.eval([self.imgs[i] for i in range(len(self.imgs))],**self.params)
        net_time = time.time() - tic
        print('total segmentation time: {}s'.format(net_time))

        outlines = []
        for mask in self.masks:
            outlines.append(utils.outlines_list(mask))
        self.outlines = outlines   

        setRUN(self)

        self.save()

    def makeFilm():
        #subprocess.run(["ffmpeg", "-l"]) 
        print()

    def launchTracking(self, iou_threshold=0.3):
        self.clip = Clip(self.masks,self.outlines,iou_threshold=iou_threshold)
        setRUN(self)
        getRUN().clip.post()
        self.clip = getRUN().clip
        plotTracking(self.imgs,self.clip,BASE_DIR)
        print("Tracking done")

    def save(self):
        n = range(len(self.imgs))
        #Save omnipose file
        if(self.saveOmniposeFiles):
            io.masks_flows_to_seg(self.imgs, self.masks, self.flows, self.styles, [f.split(".tif")[0] for f in self.files], self.chans)

        #Save masks matrix
        if(self.saveMasks):
            serializeMasks(self.masks,BASE_DIR)

        #Save outlines
        if(self.saveOutlines):
            for idx, i in enumerate(n):
                base = os.path.splitext(self.files[idx])[0]
                outlines = utils.outlines_list(self.masks[idx])
                io.outlines_to_text(base, outlines)

"""
import matplotlib.pyplot as plt
from cellpose_omni import plot
from cellpose_omni import transforms
from omnipose.utils import normalize99
nimg = len(self.imgs)
fig = plt.figure(figsize=(masks[-1].shape[-1],masks[-1].shape[-2]))
fig.patch.set_facecolor([0]*4)
for idx, i in enumerate(n):
    maski = masks[idx] # get masks
    bdi = flows[idx][-1] # get boundaries
    flowi = flows[idx][0] # get RGB flows 
    
    img0 = omnipose.utils.normalize99(imgs[i]) 

    ax = fig.add_subplot(int(np.ceil(np.sqrt(nimg))),int(np.ceil(np.sqrt(nimg))),i+1)
    overlay = plot.mask_overlay(img0, maski)
    ax.imshow(overlay, interpolation='none')
    ax.axis('off')

#plt.show()

fig = plt.figure(figsize=(1,1))
ax = fig.add_subplot()
ax.scatter(range(len(masks)),[np.max(m) for m in masks],marker="+")
plt.show()
"""