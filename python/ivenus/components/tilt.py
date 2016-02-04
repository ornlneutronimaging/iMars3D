# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar

from .AbstractComponent import AbstractComponent

class TiltCalculation(AbstractComponent):
    
    def __init__(self, workdir):
        self.workdir = workdir
        return
    
    def __call__(self, ct_series):
        workdir = self.workdir
        from .tilt import compute
        return compute(ct_series, workdir)


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
        prefix = "Applying tilt to %r" % (in_img_series.name or "",)
        N = in_img_series.nImages
        bar = progressbar.ProgressBar(
            widgets=[
                prefix,
                progressbar.Percentage(),
                progressbar.Bar(),
                ' [', progressbar.ETA(), '] ',
            ],
            max_value = N-1
        )
        from .tilt import apply
        for i,identifier in enumerate(in_img_series.identifiers):
            # skip over existing result
            if out_img_series.exists(identifier): continue
            # apply tilt
            out = outputimg(identifier)
            apply(tilt, inputimg(identifier), out, save=False)
            # remove the border
            out.data = out.data[border_pixels:-border_pixels, border_pixels:-border_pixels]
            # save to disk
            out.save()
            # progress report
            bar.update(i)
            continue
        print
        return


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
    return int(border_pixels)


# End of file
