# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar


class Component:
    pass


class Normalization(Component):
    
    def __init__(self, workdir):
        self.workdir = workdir
        return
    
    def __call__(self, ct_series, df_images, ob_images, output_img_series):
        workdir = self.workdir
        from .filters.normalizer import normalize
        normalize(ct_series, df_images, ob_images, workdir, output_img_series)
        return


class TiltCalculation(Component):
    
    def __init__(self, workdir):
        self.workdir = workdir
        return
    
    def __call__(self, ct_series):
        workdir = self.workdir
        from .tilt import compute
        return compute(ct_series, workdir)


class TiltCorrection(Component):
    
    def __init__(self, tilt):
        "tilt: tilt angle in degrees"
        self.tilt = tilt
        return
    
    def __call__(self, in_img_series, out_img_series):
        inputimg = lambda identifier: in_img_series.getImage(identifier)
        outputimg = lambda identifier: out_img_series.getImage(identifier)
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
            apply(self.tilt, inputimg(identifier), outputimg(identifier))
            # progress report
            bar.update(i)
            continue
        print
        return


# End of file
