import numpy as np
def remove_outliers_bymedian(img, outlier_indexes, boxsize=5):
    img[outlier_indexes] = np.nan
    indexes = np.where(img!=img)
    for ind1, ind2 in zip(*indexes):
        img[ind1, ind2] = np.nanmedian(img[ind1-boxsize:ind1+boxsize, ind2-boxsize:ind2+boxsize])
        continue
    return img
    
