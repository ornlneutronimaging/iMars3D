# CT data object
# A CT object contains a CT scan and OB and DF images.

import os, glob
import numpy as np
import progressbar

class CT:

    def __init__(self, path, CT_subdir=None, CT_identifier=None):
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
        self.sniff()
        return

        
    def recon(self, workdir='work', outdir='out'):
        from . import io
        # dark field
        dfs = io.imageCollection(self.DF_pattern, name="Dark Field")
        # open beam
        obs = io.imageCollection(self.OB_pattern, name="Open Beam")
        # ct
        angles = self.angles
        theta = angles * np.pi / 180.
        pattern = self.CT_pattern
        ct_series = io.ImageFileSeries(pattern, identifiers = angles, name = "CT")
        # process
        import imars3d as i3
        normalized = i3.normalize(ct_series, dfs, obs, workdir=os.path.join(workdir, 'normalization'))
        tilt_corrected = i3.correct_tilt(normalized, workdir=os.path.join(workdir, 'tilt-correction'))
        if_corrected = i3.correct_intensity_fluctuation(tilt_corrected, workdir=os.path.join(workdir, 'intensity-fluctuation-correction'))
        angles, sinograms = i3.build_sinograms(if_corrected, workdir=os.path.join(workdir, 'sinogram'))
        # take the middle part to calculate the center of rotation
        # FIXME: hard coded numbers
        sino = [s.data for s in sinograms[900:1100]]
        sino= np.array(sino)
        proj = np.swapaxes(sino, 0, 1)
        import tomopy
        rot_center = tomopy.find_center(proj, theta, emission=False, init=1024, tol=0.5)
        rot_center = rot_center[0]
        # reconstruct
        recon = i3.reconstruct(angles, sinograms, workdir=outdir, center=rot_center)
        return
        


    def sniff(self):
        self.find_OB()
        print " * found OB pattern: %s" % self.OB_pattern
        self.find_DF()
        print " * found DF pattern: %s" % self.DF_pattern
        self.find_CT()
        print " * found CT pattern: %s" % self.CT_pattern
        return
        
        
    def find_CT(self):
        CT_identifier = self.CT_identifier
        subdir = os.path.join(self.path, self.CT_subdir)
        patterns = [
            '*%s*_*_*.fits' % CT_identifier,
            '*_*_*.fits',
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
        re_pattern = '(\S+)_(\d+)_(\d+)_(\d+).fits'
        def fn2angle(fn):
            import re
            m = re.match(re_pattern, fn)
            return float('%s.%s' % (m.group(2), m.group(3)))
        fns = map(os.path.basename, files)
        angles = map(fn2angle, fns)
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
            "*%s" % CT_identifier + "*_%07.3f_*.fits",
            "*%s" % CT_identifier + "*_%.3f_*.fits",
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
                max_value = len(angles) - 1
            )
            for i, angle in enumerate(angles):
                try:
                    ifs.getFilename(angle)
                except:
                    import traceback as tb
                    tb.print_exc()
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
        return

    
    def find_OB(self):
        return self._find_pattern(
            'OB',
            subdir_candidates = ['ob', 'OB'],
            filenamepattern_candidates = ['*ob*', '*OB*'],
            )

    def find_DF(self):
        return self._find_pattern(
            'DF',
            subdir_candidates = ['df', 'DF'],
            filenamepattern_candidates = ['*df*', '*DF*'],
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
    re_pattern = '(\S+)_(\S+)_(\d+)_(\d+)_(\d+).fits'
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
