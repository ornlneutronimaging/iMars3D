import numpy as np

def calculateCropWindow(series):
    # estimate average
    ave = estimateAverage(series)
    from . import io
    def save(d, p): 
        im = io.ImageFile(p); im.data = d; im.save()
    save(ave, "estimate-ave.tiff")
    # smooth it
    from scipy import ndimage 
    sm = ndimage.median_filter(ave, 9)
    save(sm, "sm-estimate-ave.tiff")
    # find foreground rectangle
    Y, X = np.where(sm < 0.8)
    ymax = Y.max(); ymin = Y.min()
    xmax = X.max(); xmin = X.min()
    # expand it a bit
    width = xmax - xmin; height = ymax - ymin
    xmin -= width/6.; xmax += width/6.
    ymin -= height/6.; ymax += height/6.
    HEIGHT, WIDTH = ave.shape
    if xmin < 0: xmin = 0
    if xmax > WIDTH-1: xmax =WIDTH-1
    if ymin < 0: ymin = 0
    if ymax > HEIGHT-1: ymax =HEIGHT-1
    xmin, xmax, ymin, ymax = map(int, (xmin, xmax, ymin, ymax))
    return xmin, xmax, ymin, ymax



def estimateAverage(series):
    sum = None; N = 0
    for i,img in enumerate(series):
        if i%5!=0: continue # skip some
        data = img.data
        if sum is None:
            sum = np.array(data, dtype='float32')
        else:
            sum += data
        N += 1
        continue
    return sum/N


