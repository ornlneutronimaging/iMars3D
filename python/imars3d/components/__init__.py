# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar

from .AbstractComponent import AbstractComponent

class Normalization(AbstractComponent):
    
    def __init__(self, workdir):
        self.workdir = workdir
        return
    
    def __call__(self, ct_series, df_images, ob_images, output_img_series):
        workdir = self.workdir
        from ..filters.normalizer import normalize
        normalize(ct_series, df_images, ob_images, workdir, output_img_series)
        return


from .tilt import TiltCalculation, TiltCorrection


class Projection(AbstractComponent):

    def __call__(self, ct_series, sinograms):
        """convert ct image series to sinogram series"""
        N = ct_series.nImages
        img0 = ct_series[0]
        data0 = img0.data
        Y, X = data0.shape
        # array to hold all data
        import numpy as np
        data = np.zeros( (N, Y, X), dtype=float )
        # read data
        for i in range(N):
            data[i, :] = ct_series[i].data
            continue
        # 
        sinograms.identifiers = range(Y)
        for y in range(Y):
            sino = sinograms[y]
            sino.data = data[:, y, :]
            sino.save()
            continue
        return


class IntensityFluctuationCorrection(AbstractComponent):
    
    """The neutron beam intensity fluctuates and the simple normalization
using the white beam measurements is not enough. This component
should normalize the intensity using the intensities near the edges"""

    def __call__(self, input_ct_series, output_ct_series):
        import tomopy, numpy as np
        data = [img.data for img in input_ct_series]
        data = np.array(data)
        data2 = tomopy.normalize_bg(data)
        data2[data2<0] = 0
        for i, img in enumerate(output_ct_series):
            img.data = data2[i]
            img.save()
            continue
        return
        


# End of file
