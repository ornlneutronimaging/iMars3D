# CT data object
# A CT object contains a CT scan and OB and DF images.

import os, glob
import numpy as np

class CT:

    def __init__(self, path, CT_subdir=None, CT_identifier=None):
        self.path = path
        self.CT_subdir = CT_subdir or '.'
        self.CT_identifier = CT_identifier or 'CT'
        self.sniff()
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
            for angle in angles:
                try:
                    ifs.getFilename(angle)
                except:
                    bad = True
                    break
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


# End of file
