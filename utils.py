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

import cv2
def outlines_list(masks):
    """ get outlines of masks as a list to loop over for plotting """
    outpix=[]
    for n in np.unique(masks)[1:]:
        mn = masks==n
        if mn.sum() > 0:
            contours = cv2.findContours(mn.astype(np.uint8), mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
            contours = contours[-2]
            cmax = np.argmax([c.shape[0] for c in contours])
            pix = contours[cmax].astype(int).squeeze()
            if len(pix)>4:
                outpix.append(pix)
            else:
                outpix.append(np.zeros((0,2)))
    return outpix


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
