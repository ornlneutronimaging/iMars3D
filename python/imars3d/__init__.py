# iMars3D python package

from __future__ import absolute_import, division, print_function
import matplotlib as mpl; mpl.use("Agg")



# config file
# Examples
#   * tests/imars3d/tilt/imars3d.conf
#   * tests/imars3d/parallel/imars3d.conf
import yaml, os
conf_path = "imars3d.conf"
config = dict()
if os.path.exists(conf_path):
    config = yaml.load(open(conf_path))
# logging config
import logging.config
logging_conf = config.get("logging")
if logging_conf:
    logging.config.dictConfig(logging_conf)
# parallelization cofnig
parallel = config.get('parallelization')
if not parallel:
    config['parallelization'] = dict(max_nodes=20)
# have to rename. config is a subpackage
configuration = config

# top level methods
from . import io, components, decorators as dec
from . import detector_correction

def smooth(ct_series, workdir='work', parallel=True, filename_template=None, **kwds):
    if filename_template is None:
        filename_template = "smoothed_%07.3f.tiff"
    smoothed_ct = io.ImageFileSeries(
        os.path.join(workdir, filename_template), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Smoothed", mode="w"
    )    
    filter = components.Smoothing(**kwds)
    filter(ct_series, smoothed_ct, parallel=parallel)
    return smoothed_ct


def crop(ct_series, workdir='work', parallel=True, **kwds):
    cropped_ct = io.ImageFileSeries(
        os.path.join(workdir, "cropped_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Cropped", mode="w"
    )    
    filter = components.Cropping(**kwds)
    filter(ct_series, cropped_ct, parallel=parallel)
    return cropped_ct

@dec.timeit
def gamma_filter(ct_series, workdir='work', parallel=True, **kwds):
    gf_ct = io.ImageFileSeries(
        os.path.join(workdir, "gamma_filtered_%07.3f.tiff"), 
        identifiers=ct_series.identifiers, 
        decimal_mark_replacement=".",
        name="Gamma-filtered", mode="w"
    )    
    filter = components.GammaFiltering(**kwds)
    filter(ct_series, gf_ct, parallel=parallel)
    return gf_ct

@dec.timeit
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

@dec.timeit
def correct_tilt(ct_series, tilt=None, workdir='work', max_npairs=10, parallel=True):
    if tilt is None:
        tiltcalc = components.TiltCalculation(workdir=workdir, max_npairs=max_npairs)
        tilt = tiltcalc(ct_series)
    
    # only correct if the tilt is large
    if abs(tilt)>0.002:
        tiltcorrected_series = io.ImageFileSeries(
            os.path.join(workdir, "tiltcorrected_%07.3f.tiff"),
            identifiers = ct_series.identifiers,
            name = "Tilt corrected CT", mode = 'w',
        )
        tiltcorr = components.TiltCorrection(tilt=tilt)
        tiltcorr(ct_series, tiltcorrected_series, parallel=parallel)
        return tiltcorrected_series, tilt
    return ct_series, tilt

    
@dec.timeit
def correct_intensity_fluctuation(ct_series, workdir='work'):
    intfluct_corrected_series = io.ImageFileSeries(
        os.path.join(workdir, "intfluctcorrected_%07.3f.tiff"),
        identifiers = ct_series.identifiers,
        name = "Intensity fluctuation corrected CT", mode = 'w',
    )
    ifcorr = components.IntensityFluctuationCorrection()
    ifcorr(ct_series, intfluct_corrected_series)
    return intfluct_corrected_series

@dec.timeit
def build_sinograms(
        ct_series, workdir='work', 
        parallel=True, parallel_nodes=None):
    sinograms = io.ImageFileSeries(
        os.path.join(workdir, "sinogram_%i.tiff"),
        name = "Sinogram", mode = 'w',
    )
    if parallel:
        proj = components.Projection_MP(num_workers=parallel_nodes)
    else:
        proj = components.Projection()
    proj(ct_series, sinograms)
    return ct_series.identifiers, sinograms


def ring_artifact_removal_Ketcham(
        sinograms, workdir='work', parallel=True, filename_template=None, **kwds):
    if filename_template is None:
        filename_template = "rar_sino_%i.tiff"
    rar_sino = io.ImageFileSeries(
        os.path.join(workdir, filename_template), 
        identifiers=sinograms.identifiers, 
        name="RAR_Sinogram", mode="w"
    )
    filter = components.RingArtifactRemoval_Kectham(**kwds)
    filter(sinograms, rar_sino, parallel=parallel)
    return rar_sino


def reconstruct(angles, sinograms, workdir="work", filename_template = None, **kwds):
    """reconstruct

 * angles: ct scan angles in degrees
    """
    filename_template = filename_template or  "reconstructed_%i.tiff"
    recon_series = io.ImageFileSeries(
        os.path.join(workdir, filename_template),
        identifiers = sinograms.identifiers,
        name = "Reconstructed", mode = 'w',
    )
    import numpy as np
    theta = angles * np.pi / 180.
    from imars3d.recon.mpi import recon
    recon(sinograms, theta, recon_series, **kwds)
    return recon_series
