import numpy as np
def remove_outliers_bymedian(img, outlier_indexes, boxsize=5):
    """remove outliers from the given image by using median filtering
    just around the outliers. 
    - img: image npy array
    - outlier_indexes: indexes of outliers
    - boxsize: the size of the patch in which the median sampling is done
    """
    halfsize = boxsize//2
    img[outlier_indexes] = np.nan
    indexes = np.where(img!=img)
    for ind1, ind2 in zip(*indexes):
        img[ind1, ind2] = np.nanmedian(
            img[max(ind1-halfsize, 0):ind1+halfsize+1, max(ind2-halfsize, 0):ind2+halfsize+1])
        continue
    return img
