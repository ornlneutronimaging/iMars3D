# -*- python -*-
# -*- coding: utf-8 -*-

import progressbar
import os, sys, numpy as np


from .AbstractComponent import AbstractComponent


class TiltCalculation(AbstractComponent):
    def __init__(self, workdir):
        self.workdir = workdir
        return

    def __call__(self, ct_series):
        workdir = self.workdir
        from ..tilt import compute

        return compute(ct_series, workdir)


# End of file
