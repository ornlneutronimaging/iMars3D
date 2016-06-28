# iMars3D python package

from __future__ import absolute_import, division, print_function

import matplotlib as mpl; mpl.use("Agg")

import yaml, os
conf_path = "imars3d.conf"
config = dict()
if os.path.exists(conf_path):
    config = yaml.load(open(conf_path))

import logging.config
logging_conf = config.get("logging")
if logging_conf:
    logging.config.dictConfig(logging_conf)


from . import io, components
from . import detector_correction


def smooth(ct_series, workdir='work', **kwds):
    smoothed_ct = io.ImageFileSeries(
        os.path.join(workdir, "smoothed_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Smoothed", mode="w"
    )    
    filter = components.Smoothing(**kwds)
    filter(ct_series, smoothed_ct)
    return smoothed_ct


def crop(ct_series, workdir='work', **kwds):
    cropped_ct = io.ImageFileSeries(
        os.path.join(workdir, "cropped_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Cropped", mode="w"
    )    
    filter = components.Cropping(**kwds)
    filter(ct_series, cropped_ct)
    return cropped_ct


def gamma_filter(ct_series, workdir='work', **kwds):
    gf_ct = io.ImageFileSeries(
        os.path.join(workdir, "gamma_filtered_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Gamma-filtered", mode="w"
    )    
    filter = components.GammaFiltering(**kwds)
    filter(ct_series, gf_ct)
    return gf_ct


def normalize(ct_series,  dfs, obs, workdir='work'):
    normalized_ct = io.ImageFileSeries(
        os.path.join(workdir, "normalized_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Normalized", mode="w"
    )    
    normalization = components.Normalization(workdir=workdir)
    normalization(ct_series, dfs, obs, normalized_ct)
    return normalized_ct


def correct_tilt(ct_series, workdir='work'):
    tiltcalc = components.TiltCalculation(workdir=workdir)
    tilt = tiltcalc(ct_series)
    
    tiltcorrected_series = io.ImageFileSeries(
        os.path.join(workdir, "tiltcorrected_%07.3f.tiff"),
        identifiers = ct_series.identifiers,
        name = "Tilt corrected CT", mode = 'w',
    )
    tiltcorr = components.TiltCorrection(tilt=tilt)
    tiltcorr(ct_series, tiltcorrected_series)
    return tiltcorrected_series
    

def correct_intensity_fluctuation(ct_series, workdir='work'):
    intfluct_corrected_series = io.ImageFileSeries(
        os.path.join(workdir, "intfluctcorrected_%07.3f.tiff"),
        identifiers = ct_series.identifiers,
        name = "Intensity fluctuation corrected CT", mode = 'w',
    )
    ifcorr = components.IntensityFluctuationCorrection()
    ifcorr(ct_series, intfluct_corrected_series)
    return intfluct_corrected_series


def build_sinograms(ct_series, workdir='work'):
    sinograms = io.ImageFileSeries(
        os.path.join(workdir, "sinogram_%i.tiff"),
        name = "Sinogram", mode = 'w',
    )
    proj = components.Projection()
    proj(ct_series, sinograms)
    return ct_series.identifiers, sinograms


def reconstruct(angles, sinograms, workdir="work", **kwds):
    """reconstruct

 * angles: ct scan angles in degrees
    """
    recon_series = io.ImageFileSeries(
        os.path.join(workdir, "recon_%i.tiff"),
        identifiers = sinograms.identifiers,
        name = "Reconstructed", mode = 'w',
    )
    import numpy as np
    theta = angles * np.pi / 180.
    from imars3d.recon.mpi import recon
    recon(sinograms, theta, recon_series, **kwds)
    return recon_series
