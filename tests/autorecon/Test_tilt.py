#!/usr/bin/env python
# This test can only be ran after "Test_flower.py" was run

import os, glob, numpy as np
from imars3d import tilt

from imars3d.io import ImageFileSeries

dir = '/SNSlocal2/__autoreduce.CT-group-7197/intensity-fluctuation-correction/'
files = glob.glob(os.path.join(dir, '*.tiff'))
angles = [float('.'.join(os.path.splitext(os.path.basename(f))[0].split('_')[1:])) for f in files]
angles = sorted(angles)
angles = np.array(angles)

ct = ImageFileSeries(
    '/SNSlocal2/__autoreduce.CT-group-7197/intensity-fluctuation-correction/intfluctcorrected_%07.3f.tiff',
    angles, decimal_mark_replacement='_',
)
print ct[10]

tilt._compute(ct, 'tilt', calculator=tilt.direct.DirectMinimization())
# tilt._compute(ct, 'tilt', calculator=tilt.phasecorrelation.PhaseCorrelation())
# tilt._compute(ct, 'tilt', calculator=tilt.use_centers.UseCenters(sigma=15, maxshift=200))
