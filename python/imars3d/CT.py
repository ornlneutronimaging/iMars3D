# CT data object
# A CT object contains a CT scan and OB and DF images.

import os, glob
import numpy as np
import imars3d as i3
import progressbar
from . import decorators as dec
from imars3d import configuration
pb_config = configuration['progress_bar']
ct_config = configuration.get('CT', dict(clean_intermediate_files="archive"))


from .CTProcessor import CTProcessor
class CT(CTProcessor):

    """CT reconstruction engine

This is the first CTProcessor class implemented.
It uses filename patterns to find the CT/OB/DF files.

>>> ct = CT(...)
>>> ct.preprocess()
>>> ct.recon()

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

    def __init__(
            self, path, CT_subdir=None, CT_identifier=None,
            workdir='work', outdir='out', 
            parallel_preprocessing=True, parallel_nodes=None,
            clean_intermediate_files=None,
            vertical_range=None,
            ob_identifier=None, df_identifier=None,
            ob_files=None, df_files=None,
            skip_df=False,
    ):
        import logging; self.logger = logging.getLogger("CTProcessor")
        self.path = path
        if CT_subdir is not None:
            # if ct is in a subdir, its name most likely the
            # whole subdir is just for ct and no OB/DF.
            # in that case we don't usually need CT_identifier
            self.CT_subdir = CT_subdir
            self.CT_identifier = CT_identifier or '*'
        else:
            # if CT is not in a subdir, it is most likely
            # the CT files are identified by string "CT"
            self.CT_subdir = '.'
            self.CT_identifier = CT_identifier or 'CT'
        self.ob_identifier = ob_identifier
        self.df_identifier = df_identifier
        self.ob_files = ob_files
        self.df_files = df_files
        # find data paths
        self.skip_df = skip_df
        # workdir
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        self.workdir = workdir
        ct_series, angles, dfs, obs = self.sniff()
        CTProcessor.__init__(
            self,
            ct_series, angles, dfs, obs,
            workdir=workdir, outdir=outdir, 
            parallel_preprocessing=parallel_preprocessing, parallel_nodes=parallel_nodes,
            clean_intermediate_files=clean_intermediate_files,
            vertical_range=vertical_range,
            )
        return

    def sniff(self):
        """find OB/DF/CT files and constract data members
        - dfs
        - obs
        - theta (radian), angles (degree)
        - ct_series
        """
        if not self.ob_files:
            self.find_OB()
            print(" * found OB pattern: %s" % self.OB_pattern)
        else:
            self.OB_pattern = None
        if not self.skip_df:
            if not self.df_files:
                self.find_DF()
                print(" * found DF pattern: %s" % self.DF_pattern)
            else:
                self.DF_pattern = None
        self.find_CT()
        print(" * found CT pattern: %s" % self.CT_pattern)
        
        from . import io
        # dark field
        if not self.skip_df:
            dfs = io.imageCollection(glob_pattern=self.DF_pattern, files=self.df_files, name="Dark Field")
        else:
            dfs = None
        # open beam
        obs = io.imageCollection(glob_pattern=self.OB_pattern, files=self.ob_files, name="Open Beam")
        # ct
        angles = self.angles
        pattern = self.CT_pattern
        ct_series = io.ImageFileSeries(pattern, identifiers = angles, name = "CT")
        return ct_series, angles, dfs, obs
        
    CT_pattern_cache = "CT_PATTERN"
    CT_angles_cache = "CT_ANGLES.npy"
    def find_CT(self):
        pattern_cache_path = os.path.join(self.workdir, self.CT_pattern_cache)
        angles_cache_path = os.path.join(self.workdir, self.CT_angles_cache)
        if os.path.exists(pattern_cache_path) and os.path.exists(angles_cache_path):
            self.CT_pattern = open(pattern_cache_path, 'rt').read().strip()
            self.angles = np.load(angles_cache_path)
            return
        CT_identifier = self.CT_identifier
        subdir = os.path.join(self.path, self.CT_subdir)
        patterns = [
            '*%s*_*_*.*' % CT_identifier,
            '*_*_*.*',
            ]
        found = None
        for pattern in patterns:
            files = glob.glob(os.path.join(subdir, pattern))
            if len(files):
                found = pattern
                break
            continue
        if not found:
            raise RuntimeError(
                "failed to find CT images. directory: %s, patterns tried: %s"%(
                    subdir, patterns)
                )
        # routine to convert filename to angle name
        re_pattern = '(\S+)_(\d+)_(\d+)_(\d+).(\S+)'
        def fn2angle(fn):
            import re
            m = re.match(re_pattern, fn)
            if m is None:
                msg = "Failed to match pattern %r to %r. Skip" % (re_pattern, fn)
                import warnings
                warnings.warn(msg)
                return
            return float('%s.%s' % (m.group(2), m.group(3)))
        # all CT file paths following the patterns
        fns = map(os.path.basename, files)
        # convert fn to angles. skip files that cannot be converted
        angles = []
        for fn in fns:
            angle = fn2angle(fn)
            if angle is not None:
                angles.append(angle)
            continue
        # unique and ordered
        angles = set(angles)
        angles = sorted(angles)
        assert len(angles) > 2, "too few angles"
        delta = angles[1] - angles[0]
        # make sure angles are spaced correctly
        expected = np.arange(angles[0], angles[-1]+delta/2., delta)
        if len(expected) != len(angles):
            missing = [a for a in expected if not np.isclose(a, angles).any()]
            if len(missing):
                msg = "Missing angles: %s.\nStart: %s, End: %s, Step: %s" % (
                    missing, expected[0], expected[-1], delta)
                raise RuntimeError(msg)
            # nothing is missing, we are good
            angles = expected
        else:
            condition = np.isclose(
                np.arange(angles[0], angles[-1]+delta/2., delta),
                np.array(angles)
                ).all()
            assert condition, "angles not spaced correctly: %s" % (angles,)
        self.angles = np.array(angles) # in degrees
        printf_pattern_candidates = [
            "*%s" % CT_identifier + "*_%07.3f_*.*",
            "*%s" % CT_identifier + "*_%.3f_*.*",
            ]
        found = None
        for c in printf_pattern_candidates:
            from .ImageFileSeries import ImageFileSeries
            c = os.path.join(subdir, c)
            ifs = ImageFileSeries(c, angles)
            bad = False
            # progress bar
            bar = progressbar.ProgressBar(
                widgets=[
                    "Checking CT fn pattern",
                    progressbar.Percentage(),
                    progressbar.Bar(),
                    ' [', progressbar.ETA(), '] ',
                ],
                max_value = len(angles) - 1,
                **pb_config
            )
            for i, angle in enumerate(angles):
                try:
                    ifs.getFilename(angle)
                except:
                    import traceback as tb
                    m = tb.format_exc()
                    self.logger.debug("i=%s,angle=%s: %s" % (i, angle, m))
                    bad = True
                    break
                bar.update(i)
                continue
            if not bad:
                found = c
                break
            continue
        if not found:
            raise RuntimeError("Failed to find printf pattern. Filename: %s" %(
                fns[0]))
        self.CT_pattern = found
        open(pattern_cache_path, 'wt').write(found)
        np.save(angles_cache_path, self.angles)
        return

    
    def find_OB(self):
        if self.ob_identifier:
            fnp = ['*%s*' % self.ob_identifier]
        else:
            fnp = ['*ob*', '*OB*']
        return self._find_pattern(
            'OB',
            subdir_candidates = ['ob', 'OB'],
            filenamepattern_candidates = fnp,
            )

    def find_DF(self):
        if self.df_identifier:
            fnp = ['*%s*' % self.df_identifier]
        else:
            fnp = ['*df*', '*DF*']
        return self._find_pattern(
            'DF',
            subdir_candidates = ['df', 'DF'],
            filenamepattern_candidates = fnp,
            )


    def _find_pattern(self, kind, subdir_candidates, filenamepattern_candidates):
        candidates = subdir_candidates
        found = None
        for c in candidates:
            p = os.path.join(self.path, c)
            if os.path.exists(p):
                found = c; break
            continue
        if not found:
            # fall back is no subdir
            found = '.'
        setattr(self, '%s_subdir' % kind, found)
        subdir = found
        candidates = filenamepattern_candidates
        found = None
        for c in candidates:
            pattern = os.path.join(self.path, subdir, c)
            files = glob.glob(pattern)
            if files:
                found = pattern; break
            continue
        if not found:
            raise IOError("failed to find %s. patterns tried: %s" % (
                kind, filenamepattern_candidates))
        setattr(self, '%s_pattern' % kind, found)
        return

    pass


def get_ct_scan_info(files):
    re_pattern = '(\S+)_(\S+)_(\d+)_(\d+)_(\d+).(\S+)'
    def _(fn):
        import re
        m = re.match(re_pattern, fn)
        if not m: return
        angle = float('%s.%s' % (m.group(3), m.group(4)))
        date = m.group(1)
        name = m.group(2)
        return date, name, angle
    fns = map(os.path.basename, files)
    info = map(_, fns)
    return info

# End of file
