#!/usr/bin/env python

import numpy as np

def getBg(img, **kwds):
    from skimage import feature
    edge = feature.canny(img.data, **kwds)
    start_row = None
    middle_col = (edge.shape[1]-1)//2
    start_cols = np.ones(edge.shape[0], dtype=int)*middle_col
    stop_cols = np.ones(edge.shape[0], dtype=int)*middle_col
    for i, row in enumerate(edge):
        isedge = row > 0
        if isedge.any():
            w = np.where(isedge)[0]
            start_cols[i], stop_cols[i] = w[0], w[-1]
            # set the row that starts to have object to be measured
            if start_row is None:
                start_row = i
            stop_row = i+1
        continue
    print(start_row, stop_row)
    # for start, stop in zip(start_cols, stop_cols):
    #    print(start, stop)
    #    continue
    from matplotlib import pyplot as plt
    plt.plot(start_cols, '.')
    plt.plot(stop_cols, '.')
    plt.savefig("edge.png")
    return
