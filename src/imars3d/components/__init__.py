# -*- python -*-
# -*- coding: utf-8 -*-


"""
Components should have the method __call__ with input and output image series
as the parameters.
"""

import progressbar

from .AbstractComponent import AbstractComponent


class Smoothing(AbstractComponent):

    def __init__(self, **kwds):
        self.kargs = kwds
        return
    
    def __call__(self, ct_series, output_series, parallel=True):
        if parallel:
            from ..filters.smoothing import filter_parallel as filter
        else:
            from ..filters.smoothing import filter
        filter(ct_series, output_series, **self.kargs)
        return


class Cropping(AbstractComponent):

    def __init__(self, box):
        self.box = box
        return
    
    def __call__(self, ct_series, output_series, parallel=True):
        if parallel:
            from ..filters.cropping import filter_parallel as filter
        else:
            from ..filters.cropping import filter
        filter(ct_series, output_series, box = self.box)
        return


class GammaFiltering(AbstractComponent):
    
    def __init__(self, boxsize=5):
        self.boxsize = boxsize
        return
    
    def __call__(self, ct_series, output_img_series, parallel=True):
        boxsize = self.boxsize
        if parallel:
            from ..filters.gamma_filtering import filter_parallel as filter
        else:
            from ..filters.gamma_filtering import filter
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
from .projection import Projection, Projection_MP


class IntensityFluctuationCorrection(AbstractComponent):
    
    """The neutron beam intensity fluctuates and the simple normalization
using the white beam measurements is not enough. This component
should normalize the intensity using the intensities near the edges"""

    def __call__(self, ct_series, output_series, parallel=True):
        if parallel:
            from ..filters.ifc import filter_parallel as filter
        else:
            from ..filters.ifc import filter
        filter(ct_series, output_series, sigma=3)
        return

    def __call__usingtomopy(self, input_ct_series, output_ct_series):
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


class RingArtifactRemoval_Kectham(AbstractComponent):

    def __init__(self, **kwds):
        self.kargs = kwds
        return
    
    def __call__(self, sinograms, output_sinograms, parallel=True):
        if parallel:
            from ..filters.ring_artifact_removal_Ketcham import filter_parallel as filter
        else:
            from ..filters.ring_artifact_removal_Ketcham import filter
        filter(sinograms, output_sinograms, **self.kargs)
        return


# End of file
