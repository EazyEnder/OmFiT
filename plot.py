import matplotlib.image as mpimg
from GlobalStorage import getRUN
import matplotlib.pyplot as plt
from cellpose_omni import plot
import time
from utils import printProgressBar
import numpy as np
def plotTracking(imgs,clip,export_path):
    print("Plot")
    tic = time.time() 
    for i in range(len(imgs)):
        printProgressBar(i,len(imgs))
        img = imgs[i]
        cells = clip.states[i]
        plt.clf()
        centers = np.array([c.center for c in cells]).T
        colors = [c.color for c in cells]
        #plotLineUsingFAM(clip,i)
        overlay = plot.mask_overlay(img, getRUN().clip.buildMask(i).astype(int))
        plt.imshow(overlay, interpolation='none')
        #plt.imshow(img)
        plt.scatter(centers[1],centers[0],c=colors)
        plt.savefig(export_path+"/export_"+str(i)+".jpg")
    net_time = time.time() - tic
    print(f'Plot done ({np.round(net_time,2)}s)')

def plotLineUsingFAM(clip,time,time_forward=1.):
    FAM = clip.fam_weights
    for cell_fam in FAM[time]:
        fam_t = []
        for tpl in cell_fam[1]:
            if(tpl[0].time == cell_fam[0].time+time_forward):
                fam_t.append((tpl[0].center,tpl[1]))
        for ft in range(len(fam_t)):
            if(ft == 0):
                continue
            fam = fam_t[ft]
            line = [fam[0],cell_fam[0].center]
            thickness = fam[1]
            line = np.array(line).T
            plt.plot(line[1],line[0],alpha=np.power(thickness,0.5),color=cell_fam[0].color)