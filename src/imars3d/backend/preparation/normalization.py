#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import param
import multiprocessing
import numpy as np
import tomopy


logger = param.get_logger(__name__)
logger.name = __name__


class normalization(param.ParameterizedFunction):
    """
    Normalize the input array(s) by subtracting the dark field and dividing by the adjusted flat field.

    Parameters
    ----------
    arrays:
        3D array of images, the first dimension is the rotation angle omega.
    flats:
        3D array of flat field images (aka flat field, open beam), axis=0 is the image number axis.
    darks:
        3D array of dark field images, axis=0 is the image number axis.
    cut_off:
        Permitted maximum value for the normalized data, originated from tomopy, negative values means no cutoff.
    max_workers:
        number of cores to use for parallel processing, default is 0, which means using all available cores.

    Returns
    -------
        normalized 3D array of images, the first dimension is the rotation angle omega.
    """

    arrays = param.Array(doc="3D array of images, the first dimension is the rotation angle omega.")
    flats = param.Array(
        doc="3D array of flat field images (aka flat field, open beam), axis=0 is the image number axis."
    )
    darks = param.Array(doc="3D array of dark field images, axis=0 is the image number axis.")
    cut_off = param.Number(
        default=-1.0,
        doc="Permitted maximum value for the normalized data, originated from tomopy, negative values means no cutoff.",
    )
    max_workers = param.Integer(
        default=0,
        bounds=(0, None),
        doc="Maximum number of processes allowed during loading",
    )

    def __call__(self, **params):
        logger.info(f"Executing Filter: Normalization")
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # import pdb; pdb.set_trace()
        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = multiprocessing.cpu_count() if params.max_workers <= 0 else params.max_workers
        logger.debug(f"max_worker={self.max_workers}")

        # parse input (mostly for Tomopy)
        tomopy_cut_off = None if params.cut_off < 0 else float(params.cut_off)
        # use median filter to remove outliers from flats and darks
        # NOTE: this will remove the random noises coming from the environment.
        self.flats = np.median(params.flats, axis=0)
        self.darks = np.median(params.darks, axis=0)
        # apply normalization
        # NOTE:
        # For pixels where dark > flat, tomopy replace the value with 1e-6 on-the-fly
        # see https://github.com/tomopy/tomopy/blob/master/source/tomopy/prep/normalize.py#L135
        #
        arrays_normalized = tomopy.normalize(
            params.arrays, self.flats, self.darks, cutoff=tomopy_cut_off, ncore=self.max_workers
        )
        # return
        logger.info(f"FINISHED Executing Filter: Normalization")

        return arrays_normalized
