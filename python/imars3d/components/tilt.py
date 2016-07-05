# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar

from .AbstractComponent import AbstractComponent

class TiltCalculation(AbstractComponent):
    
    def __init__(self, workdir, max_npairs=10):
        self.workdir = workdir
        self.max_npairs = max_npairs
        return
    
    def __call__(self, ct_series):
        workdir = self.workdir
        from ..tilt import compute
        return compute(ct_series, workdir, max_npairs=self.max_npairs)


class TiltCorrection(AbstractComponent):
    
    def __init__(self, tilt):
        "tilt: tilt angle in degrees"
        self.tilt = tilt
        return
    
    def __call__(self, in_img_series, out_img_series):
        tilt = self.tilt
        inputimg = lambda identifier: in_img_series.getImage(identifier)
        outputimg = lambda identifier: out_img_series.getImage(identifier)
        # compute border pixels
        inimgsize = max(inputimg(in_img_series.identifiers[0]).data.shape)
        border_pixels = _calc_border_pixels(tilt, inimgsize)
        # 
        from ..filters.batch import filter
        DESC = "Applying tilt"
        return filter(
            in_img_series, out_img_series, DESC, apply_tilt_oneimg,
            tilt=tilt, border=border_pixels)


def apply_tilt_oneimg(img, tilt=None, border=None):
    """apply tilt to the given image
    """
    from scipy import ndimage
    import numpy as np
    data = ndimage.rotate(img, -tilt)
    return data[border:-border, border:-border]


def _calc_border_pixels(angle, size):
    """angle is in degrees
    
    Whe the image is rotated, scipy will return a larger image that 
    has borders around the original image. 
    4 triangles show about on the edge with zeros in them.
    since the tilt angle is always small, we can simply take 
    a square cut at the center of that image.

    so there are three squares:
    * original square A from the input image
    * the sqaure returned by scipy, B. it is larger than A, and it is at "angle"
      with respect to A
    * sqaure C to be the output image. it is at "angle" with respect to
      A, and parallel to B. it is the smallest.

    the sizes have the following relations
    B = A(cos theta + sin theta)
    A = C(cos theta + sin theta)
    """
    from math import pi, sin, cos
    t = abs(angle * pi / 180)
    factor = cos(t) + sin(t)
    B = size * factor
    C = size / factor
    border_pixels = (B-C)/2 + 1
    # border_pixels *= 1.2
    return int(border_pixels)


# End of file
