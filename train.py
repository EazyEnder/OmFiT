from PIL import Image
import numpy as np

def normalizeImgs(files):
    for file in files:
        img = Image.open('file')
        arr = np.array(img)
        indexes = arr.unique().sort()
        normalized = range(1,len(indexes)+1)
        for i in range(len(arr)):
            for j in range(len(arr[i])):
                pixel = arr[i,j]
                if(pixel == 0):
                    continue
                ind = np.where(indexes == pixel)
                arr[i,j] = normalized[ind]
        norm_img = Image.fromarray(arr)
        norm_img.save(file.split(".")[0]+"_norm.tif")