import numpy as np

def calculateCropWindow(series, normalize=False):
    # estimate average
    ave = estimateAverage(series)
    from . import io
    def save(d, p): 
        im = io.ImageFile(p); im.data = d; im.save()
    save(ave, "estimate-ave.tiff")
    # smooth it
    from scipy import ndimage 
    sm = ndimage.median_filter(ave, 9) # 21)
    save(sm, "sm-estimate-ave.tiff")
    # make sure all numbers are smaller than 1.
    if normalize:
        max = np.max(sm);  sm/=max
    else:
        sm[sm>1] = 1
    # get background intensities
    left = sm[:, :10];    left_median = np.median(left)
    top = sm[:10, :];     top_medain = np.median(top)
    right = sm[:, -10:];  right_median = np.median(right)
    bottom = sm[-10:, :]; bottom_median = np.median(bottom)
    #
    background_int = np.median([left_median, top_medain, right_median, bottom_median])
    # if background is dark
    if background_int < .08:
        max_bg = np.max(map(np.max, [left, top, right, bottom]))
        max_bg = np.max( (max_bg, 0.1) )
        Y1, X1 = np.where(sm>max_bg)
        xmin = np.min(X1); xmax = np.max(X1)
        ymin = np.min(Y1); ymax = np.max(Y1)
        return xmin, xmax, ymin, ymax
    # there might be outliers in borders, just clear the borders out
    sm[:, :25] = background_int;   sm[:25, :] = background_int
    sm[:, -25:] = background_int;   sm[-25:, :] = background_int
    # find rectangle for real data
    Y, X = np.where(sm < background_int*0.95)
    ymax = Y.max(); ymin = Y.min()
    xmax = X.max(); xmin = X.min()
    # expand it a bit
    width = xmax - xmin; height = ymax - ymin
    expand_ratio = .1
    xmin -= width*expand_ratio; xmax += width*expand_ratio
    ymin -= height*expand_ratio; ymax += height*expand_ratio
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


