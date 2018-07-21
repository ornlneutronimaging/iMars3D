# CTProcessor class

import os, glob
import numpy as np
import imars3d as i3
import progressbar
from . import decorators as dec
from imars3d import configuration
pb_config = configuration['progress_bar']
ct_config = configuration.get('CT', dict(clean_intermediate_files="archive"))


class CTProcessor:

    __processor_doc__ = """
Intermediate results are saved as object variables

* gamma_filtered
* normalized
* cropped
* if_corrected
* tilt_corrected
* sigogram

Reults:

* reconstructed
* recon_RAR

Customizing preprocessors:

>>> ct = CT(...)
>>> ct.gamma_filter = False # no gamma filtering
>>> ct.gamma_filter = my_gamma_filter # use my own gamma filter
>>> ct.normalizer = ... # similarly for normalizer
>>> ct.preprocess()
>>> ct.recon()

By default, intermediate results will be moved over to the disk where the outputs are (outdir) after CT reconstruction is all done:

    clean_intermediate_files='archive'

or they can be cleaned on the fly to save disk usage:

    clean_intermediate_files='on_the_fly"

or they can be kept where it is:

    clean_intermediate_files=False

and you will need to clean them up yourself.
The default behavior can be modified by configuration file "imars3d.conf".
"""

    __doc__ = """CT reconstruction processor
    
>>> ct = CTProcessor(ct_series, angles, dfs, obs, **kwds)
>>> ct.preprocess()
>>> ct.recon()
""" + __processor_doc__
    

    def __init__(
            self,
            ct_series, angles, dfs, obs,
            workdir='work', outdir='out', 
            parallel_preprocessing=True, parallel_nodes=None,
            clean_intermediate_files=None,
            vertical_range=None,
    ):
        self.ct_series = ct_series
        self.dfs = dfs
        self.obs = obs
        self.angles = angles
        self.theta = angles * np.pi / 180.
        
        # workdir
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        self.workdir = workdir
        # outdir
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        self.outdir = outdir
        #
        self._init_processing_params(parallel_preprocessing, parallel_nodes, clean_intermediate_files, vertical_range)
        self.r = results()
        return


    def _init_processing_params(
            self, parallel_preprocessing, parallel_nodes, clean_intermediate_files, vertical_range):
        self.parallel_preprocessing = parallel_preprocessing
        self.parallel_nodes = parallel_nodes
        if clean_intermediate_files is None:
            clean_intermediate_files = ct_config['clean_intermediate_files']
        assert clean_intermediate_files in ['on_the_fly', 'archive', False]
        self.clean_intermediate_files = clean_intermediate_files
        self.vertical_range = vertical_range
        return

    gamma_filter = None
    normalizer = None

    @dec.timeit
    def preprocess(self, workdir=None, outdir=None):
        workdir = workdir or self.workdir
        outdir = outdir or self.outdir
        # get image objs
        dfs = self.dfs; obs = self.obs
        ct_series = self.ct_series
        theta = self.theta
        # preprocess
        # this allows gamma_filter to be turned off if user set ct.gamma_filter=False
        if self.gamma_filter is not False:
            # this allows user to set a custom gamma_filter function
            if self.gamma_filter is None:
                # the default gamma filter
                self.gamma_filter = i3.gamma_filter
            gamma_filter = self.gamma_filter
            # run gamma filtering
            gamma_filtered = gamma_filter(
                ct_series, workdir=os.path.join(workdir, 'gamma-filter'),
                parallel = self.parallel_preprocessing)
        else:
            # no filtering
            gamma_filtered = ct_series
        #
        # similarly, we allow customization of the normalizer
        if self.normalizer is not False:
            if self.normalizer is None:
                self.normalizer = i3.normalize
            normalizer = self.normalizer
            normalized = normalizer(gamma_filtered, dfs, obs, workdir=os.path.join(workdir, 'normalization'))
        else:
            normalized = gamma_filtered
        if self.clean_intermediate_files=='on_the_fly' and gamma_filtered is not ct_series:
            gamma_filtered.removeAll()
        # save references
        self.r.gamma_filtered = gamma_filtered
        self.r.normalized = normalized
        return normalized


    def recon(self,
              workdir=None, outdir=None, outfilename_template=None,
              tilt=None, crop_window=None,
              smooth_projection=None, remove_rings_at_sinograms=None,
              smooth_recon=None, remove_rings=None,
              **kwds):
        """Run CT reconstruction workflow

    Parameters:
        * workdir: fast work dir
        * outdir: output dir. can be at a slower disk
        * crop_window: (xmin, ymin, xmax, ymax)
        * remove_rings_at_sinograms: remove ring artifacts by filtering sinograms
          - if ==False, no filtering
          - if is True, filtering with default parameters
          - if is a dictionary, will be used as kwd arguments for filtering component
            e.g. dict(average_window_size=20, Nsubsets=10, correction_range=(0.9, 1.1))
        * smooth_recon: smooth the reconstruction result
          - if ==False, no smoothing
          - if is True, smoothing with default parameters
          - if is a dictionary, will be used as kwd arguments for smoothing component
            e.g. dict(algorithm='bilateral', sigma_color=0.0005, sigma_spatial=5)
        * smooth_projection: extra smoothing of projection
          - if ==False, no smoothing
          - if is True, smoothing with default parameters
          - if is a dictionary, will be used as kwd arguments for smoothing component
            e.g. dict(algorithm='bilateral', sigma_color=0.02, sigma_spatial=5)

    Default processing chain:
        * preprocess
          - gamma filtering
          - normalization
        * crop
        * median-filter (size 3)
        * (optional) smooth: by default, use bilateral filter
        * intensity fluctuation correction
        * tilt correction
        * create sinograms
        * (optional) apply ring-artifact-removal filter to sinograms
        * find center of rotation
        * reconstruction
        * (optional) smooth reconstruction
        """
        workdir = workdir or self.workdir;  outdir = outdir or self.outdir
        # preprocess
        pre = self.preprocess(workdir=workdir, outdir=outdir)
        # crop
        if crop_window is None:
            # auto-cropping
            cropped = self.autoCrop(pre)
        else:
            xmin, ymin, xmax, ymax = crop_window
            cropped = self.crop(
                pre, 
                left=xmin, right=xmax, top=ymin, bottom=ymax)
        if self.clean_intermediate_files == 'on_the_fly':
            pre.removeAll()
        # median filter
        self.r.median_filtered = median_filtered = self.smooth(
            cropped, outname='median_filtered', algorithm='median', size=3)
        if smooth_projection:
            if smooth_projection is True:
                # default smooth
                smooth_projection = dict(algorithm='bilateral', sigma_color=0.02, sigma_spatial=5)
            pre = smoothed = self.smooth(median_filtered, outname='smoothed', **smooth_projection)
            self.r.smoothed_projection = smoothed
        else:
            pre = median_filtered
        # correct intensity fluctuation
        if_corrected = i3.correct_intensity_fluctuation(
            pre, workdir=os.path.join(workdir, 'intensity-fluctuation-correction'))
        if self.clean_intermediate_files == 'on_the_fly':
            pre.removeAll()
        # correct tilt
        pre = if_corrected
        if tilt is None:
            tilt_corrected, tilt = self.correctTilt_loop(
                pre, workdir=workdir)
        else:
            tilt_corrected, tilt = i3.correct_tilt(
                pre, tilt=tilt, 
                workdir=os.path.join(workdir, 'tilt-correction' ),
                max_npairs=None, parallel=self.parallel_preprocessing)
        if self.clean_intermediate_files == 'on_the_fly':
            pre.removeAll()
        #
        self.r.cropped = cropped
        self.r.if_corrected = if_corrected
        self.r.tilt_corrected = tilt_corrected
        # reconstruct
        outfilename_template = outfilename_template or "recon_%04d.tiff"
        recon = self.reconstruct(
            tilt_corrected,
            workdir=workdir, outdir=outdir,
            remove_rings_at_sinograms=remove_rings_at_sinograms,
            outfilename_template=outfilename_template,
            **kwds)
        if smooth_recon:
            if smooth_recon is True:
                smooth_recon = dict(algorithm='bilateral', sigma_color=0.0005, sigma_spatial=5)
            from . import smooth
            recon = self.r.sm_recon = smooth(
                recon, workdir=os.path.join(self.outdir, 'smoothed'),
                parallel = self.parallel_preprocessing,
                filename_template='sm_' + outfilename_template,
                **smooth_recon)
        if remove_rings:
            self.removeRings(recon)
        # clean up
        import shutil
        if self.clean_intermediate_files == 'archive':
            import datetime
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            newpath = os.path.join(outdir, 'work-%s' % now)
            shutil.move(workdir, newpath)
            # create a soft link so that the intermediate data can still be accessed
            # from the CT object
            os.symlink(newpath, workdir)
        elif self.clean_intermediate_files == 'on_the_fly':
            shutil.rmtree(workdir)
        return


    def calculateTilt(self, workdir, calculator=None, image_series=None, **kwds):
        """calculate tilt

* workdir: working directory
* calculator: "direct" or "phasecorrelation"
* image_series: by default self.cropped
"""
        from . import tilt
        if calculator == 'direct':
            calculator = tilt.direct.DirectMinimization()
        elif calculator == 'phasecorrelation':
            calculator = tilt.phasecorrelation.PhaseCorrelation()
        if image_series is None:
            image_series = self.r.if_corrected
        return tilt._compute(image_series, workdir, calculator=calculator, **kwds)


    def removeRings(self, reconned=None, outdir=None, outfilename_template=None, **kwds):
        "remove rings as a post-processing step"
        if outdir is None:
            outdir = os.path.join(self.outdir, 'rar_direct')
            if not os.path.exists(outdir):
                os.makedirs(outdir)
        import tomopy
        # input
        if reconned is None: reconned = self.r.reconstructed
        # output
        outfilename_template = outfilename_template or "rar_direct_%i.tiff"
        from . import io
        corrected_ifs = io.ImageFileSeries(
            os.path.join(outdir, outfilename_template),
            identifiers = reconned.identifiers,
            name = "Ring-artifact-directly-removed reconstruction", mode = 'w',
        )
        # process in chunks
        N = len(reconned)
        step = 100
        for istep in range(N//step+1):
            start = step*istep; end = step*(istep+1)
            if end > N: end = N
            if end <=start: continue
            # build array
            stack = np.array([im.data for im in reconned[start:end]])
            corrected = tomopy.remove_ring(stack, **kwds)
            for i in range(corrected.shape[0]):
                img = corrected_ifs[istep*step+i]
                img.data = corrected[i]
                img.save()
                continue
            continue
        self.r.recon_rar_direct = corrected_ifs
        return self.r.recon_rar_direct
            

    def correctTilt_loop(self, pre, workdir):
        # correct tilt
        MAX_TILT_ALLOWED = 0.05
        NROUNDS = 3
        for i in range(NROUNDS):
            tilt_corrected, tilt = i3.correct_tilt(
                pre, workdir=os.path.join(workdir, 'tilt-correction-%s' % i),
                max_npairs=None, parallel=self.parallel_preprocessing)
            if self.clean_intermediate_files == 'on_the_fly':
                pre.removeAll()
            if abs(tilt) < MAX_TILT_ALLOWED: break
            pre = tilt_corrected
            continue
        if abs(tilt) >= MAX_TILT_ALLOWED:
            msg = "failed to bring tilt down to less than %s degrees in %s rounds" % (MAX_TILT_ALLOWED, NROUNDS)
            # raise RuntimeError(msg)
            import warnings
            warnings.warn(msg)
        return tilt_corrected, tilt

    @dec.timeit
    def autoCrop(self, series):
        from .autocrop import calculateCropWindow
        xmin, xmax, ymin, ymax = calculateCropWindow(series)
        # crop
        return self.crop(series, left=xmin, right=xmax, top=ymin, bottom=ymax)


    def crop(self, series, left=None, right=None, top=None, bottom=None):
        Y,X = self.ct_series[0].data.shape
        left = left or 0
        right = right or X
        top = top or 0
        bottom = bottom or Y
        box = left, right, top, bottom
        from . import crop
        return crop(
            series, workdir=os.path.join(self.workdir, 'crop'), box=box,
            parallel = self.parallel_preprocessing)


    @dec.timeit
    def smooth(self, series, outname='smoothed', **kwds):
        from . import smooth
        return smooth(
            series, workdir=os.path.join(self.workdir, outname),
            parallel = self.parallel_preprocessing,
            **kwds)


    @dec.timeit
    def reconstruct(
            self, 
            ct_series, workdir=None, outdir=None,
            rot_center=None, explore_rot_center=True,
            outfilename_template=None,
            remove_rings_at_sinograms=False,
            mirror=True,
            **kwds):
        workdir = workdir or self.workdir;  
        outdir = outdir or self.outdir
        theta = self.theta
        # preprocess
        angles, sinograms = i3.build_sinograms(
            ct_series, workdir=os.path.join(workdir, 'sinogram'),
            parallel = self.parallel_preprocessing,
            parallel_nodes = self.parallel_nodes)
        # take the middle part to calculate the center of rotation
        NSINO = len(sinograms)
        sino = [s.data for s in sinograms[NSINO//3: NSINO*2//3]]
        # sino = [s.data for s in sinograms]
        sino= np.array(sino)
        proj = np.swapaxes(sino, 0, 1)
        import tomopy
        X = proj.shape[-1]
        DEVIATION = 40 # max deviation of rot center from center of image
        if explore_rot_center:
            print("* Exploring rotation center using tomopy...")
            dpath=os.path.join(workdir, 'tomopy-findcenter')
            if not os.path.exists(dpath): # skip if already done
                tomopy.write_center(
                    proj.copy(), theta,
                    cen_range=[X//2-DEVIATION, X//2+DEVIATION, 1.],
                    dpath=dpath,
                    emission=False)
        if rot_center is None:
            print("* Computing rotation center using 180deg pairs...")
            from .tilt import find_rot_center
            rot_center = find_rot_center.find(
                ct_series, workdir=os.path.join(workdir, 'find-rot-center'))
        print('* Rotation center: %s' % rot_center)
        self.rot_center = rot_center
        open(os.path.join(workdir, 'rot_center'), 'wt').write(str(rot_center))
        # reconstruct 
        if self.vertical_range:
            sinograms = sinograms[self.vertical_range]
        self.r.sinograms = sinograms
        # sometimes the rotation angles and the stacking sequence coulb be not in the right convention
        if mirror:
            angles = -np.array(angles)
        # reconstruct using original sinograms
        recon = i3.reconstruct(
            angles, sinograms, 
            workdir=outdir, filename_template=outfilename_template,
            center=rot_center,
            nodes=self.parallel_nodes,
            **kwds)
        self.r.reconstructed = recon
        # reconstruct using rar filtered sinograms
        if remove_rings_at_sinograms:
            if remove_rings_at_sinograms is True:
                remove_rings_at_sinograms = {}
            self.r.rar_sino = sinograms = i3.ring_artifact_removal_Ketcham(
                sinograms, workdir=os.path.join(workdir, 'rar_sinograms'),
                parallel = self.parallel_preprocessing,
                **remove_rings_at_sinograms)
            recon = i3.reconstruct(
                angles, sinograms, 
                workdir=os.path.join(outdir, 'rar_sinograms'),
                filename_template=outfilename_template,
                center=rot_center,
                nodes=self.parallel_nodes,
                **kwds)
            self.r.reconstructed_using_rar_sinograms = recon
        return recon


    pass


class results:
    pass


# End of file
