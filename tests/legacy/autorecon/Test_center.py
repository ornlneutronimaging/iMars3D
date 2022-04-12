#!/usr/bin/env python
import os, glob, numpy as np
from imars3d import tilt

from imars3d.io import ImageFileSeries

dir = "/SNSlocal2/__autoreduce.CT-group-7197/tilt-correction-1/"
files = glob.glob(os.path.join(dir, "*.tiff"))
angles = [float(".".join(os.path.splitext(os.path.basename(f))[0].split("_")[1:])) for f in files]
angles = sorted(angles)
angles = np.array(angles)

ct = ImageFileSeries(
    "/SNSlocal2/__autoreduce.CT-group-7197/tilt-correction-1/tiltcorrected_%07.3f.tiff",
    angles,
    decimal_mark_replacement="_",
)
print(ct[10])

from imars3d.tilt import find_rot_center

find_rot_center.find(ct, workdir="_tmp.center", max_npairs=20)
