import numpy as np

def ignoreMerge(masks, force, times=None):
    """masks = list of matrix;
    force = boolean, if True then the problematic image will be replaced with the older one else the program will return the mean of older and newer cell border """

    if(times==None):
        times=range(1,len(masks)+1)
    count = [np.max(m) for m in masks]
    for m in range(len(masks)):
        if(count[m] - count[m-1] < 0):

            
            break
    return None

def getCtrdGradient(list,index,amplitude):
    bkwd = getBkwdGradient(list,index,amplitude)
    frwd = getFrwdGradient(list,index,amplitude)
    return np.concatenate(bkwd,[0],frwd)

def getBkwdGradient(list,index,amplitude):
    grad = []
    for i in range(amplitude):
        j = index - i
        if(j<0):
            return grad
        grad.append(list[index]-list[j])
    return np.array(grad)

def getFrwdGradient(list,index,amplitude):
    grad = []
    for i in range(amplitude):
        j = index + i
        if(j>=len(list)):
            return grad
        grad.append(list[j]-list[index])
    return np.array(grad)