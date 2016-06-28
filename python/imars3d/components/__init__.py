# -*- python -*-
# -*- coding: utf-8 -*-


"""
Components should have the method __call__ with input and output image series
as the parameters.
"""

import progressbar

from .AbstractComponent import AbstractComponent


class Smoothing(AbstractComponent):

    def __init__(self, size):
        self.size = size
        return
    
    def __call__(self, ct_series, output_series):
        from ..filters.smoothing import filter_parallel as filter
        filter(ct_series, output_series, size = self.size)
        return


class Cropping(AbstractComponent):

    def __init__(self, box):
        self.box = box
        return
    
    def __call__(self, ct_series, output_series):
        from ..filters.cropping import filter
        filter(ct_series, output_series, box = self.box)
        return


class GammaFiltering(AbstractComponent):
    
    def __init__(self, boxsize=5):
        self.boxsize = boxsize
        return
    
    def __call__(self, ct_series, output_img_series):
        boxsize = self.boxsize
        from ..filters.gamma_filtering import filter_parallel as filter
        filter(ct_series, output_img_series, boxsize=boxsize)
        return


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
        data = np.zeros( (N, Y, X), dtype="float32")
        # read data
        for i in range(N):
            data[i, :] = ct_series[i].data
            continue
        # 
        prefix = "Computing sinograms from %r" % (ct_series.name or "",)
        bar = progressbar.ProgressBar(
            widgets=[
                prefix,
                progressbar.Percentage(),
                progressbar.Bar(),
                ' [', progressbar.ETA(), '] ',
            ],
            max_value = Y - 1
        )
        from ..filters.smoothing import filter_one as smooth
        sinograms.identifiers = range(Y)
        for y in range(Y):
            sino = sinograms[y]
            if sinograms.exists(y):
                print("%s already existed" % sino)
                bar.update(y)
                continue
            sino.data = data[:, y, :]
            sino.data = smooth(sino.data, 5)
            sino.save()
            bar.update(y)
            continue
        return


class IntensityFluctuationCorrection(AbstractComponent):
    
    """The neutron beam intensity fluctuates and the simple normalization
using the white beam measurements is not enough. This component
should normalize the intensity using the intensities near the edges"""

    def __call__allsametime(self, input_ct_series, output_ct_series):
        print("Intensity fluctuation correction...")
        import tomopy, numpy as np
        data = [img.data for img in input_ct_series]
        data = np.array(data)
        data2 = tomopy.normalize_bg(data)
        data2[data2<0] = 0
        for i, identifier in enumerate(output_ct_series.identifiers):
            img = output_ct_series.getImage(identifier)
            # skip over existing result
            if output_ct_series.exists(identifier):
                print("%s already existed" % img)
                continue
            img.data = data2[i]
            img.save()
            continue
        print("done")
        return


    def __call__(self, input_ct_series, output_ct_series):
        import tomopy, numpy as np
        prefix = "Perform intensity fluctuation correction on %r" % (input_ct_series.name or "",)
        bar = progressbar.ProgressBar(
            widgets=[
                prefix,
                progressbar.Percentage(),
                progressbar.Bar(),
                ' [', progressbar.ETA(), '] ',
            ],
            max_value = len(input_ct_series) - 1
        )
        for i, identifier in enumerate(output_ct_series.identifiers):
            img = output_ct_series.getImage(identifier)
            # skip over existing result
            if output_ct_series.exists(identifier):
                print("%s already existed" % img)
                bar.update(i)
                continue
            inimg = input_ct_series[i]
            data = np.array([inimg.data])
            data2 = tomopy.normalize_bg(data)[0]
            data2[data2<0] = 0
            img.data = data2
            img.save()
            bar.update(i)
            continue
        print()
        return
        


# End of file
