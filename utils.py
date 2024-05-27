import numpy as np

def computeCenters(outlines):
    """Compute bacteries center using their outlines.
    Return centers as a list"""
    centers = []
    for outline in outlines:
        center = [0,0]
        for i in range(len(outline)):
            point = outline[i]
            center[0] += point[0]
            center[1] += point[1]
        center = np.array(center)
        center /= len(outline)
        centers.append(center)
    return centers

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import time
def plotTracking(imgs,clip,export_path):
    print("Plot")
    tic = time.time() 
    for i in range(len(imgs)):
        printProgressBar(i,len(imgs))
        img = imgs[i]
        cells = clip.states[i]
        plt.clf()
        plt.imshow(img)
        centers = np.array([c.center for c in cells]).T
        colors = [c.color for c in cells]
        plotLineUsingFAM(clip,i)
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


def serializeMasks(masks,folder,times=None):
    """Serialize masks of an image set to a file.
    Each line has an img's frame time, max_components,.. (sep: ';')
    and has a matrix with sep ',' between elements and '|' between lines """

    file = open(folder+"/masks.txt","w")

    string = ""
    t = 0
    for k in range(len(masks)):
        mask = masks[k]
        t = k+1
        if(times != None):
            t = times[k]
        string += str(t)
        string += ";"
        string += str(np.max(mask))
        string += ";"
        for i in range(len(mask)):
            for j in range(len(mask[i])):
                ele = mask[i,j]
                string += str(ele)
                if(j != len(mask[i])-1):
                    string += ","
            if(i != len(mask)-1):
                string += "|"
        string += "\n"

    file.write(string)
    file.close()
    return string

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 10, fill = '#', printEnd = "\r"):
    """Print a progress bar"""
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    if iteration == total: 
        print()