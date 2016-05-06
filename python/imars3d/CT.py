# CT data object
# A CT object contains a CT scan and OB and DF images.

import os, glob
import numpy as np

class CT:

    def __init__(self, path):
        self.path = path
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
        pattern = '*CT*_*_*.fits'
        files = glob.glob(os.path.join(self.path, pattern))
        re_pattern = '(\S+)_(\d+)_(\d+)_(\d+).fits'
        def fn2angle(fn):
            import re
            m = re.match(re_pattern, fn)
            return float('%s.%s' % (m.group(2), m.group(3)))
        fns = map(os.path.basename, files)
        angles = map(fn2angle, fns)
        angles = sorted(angles)
        assert len(angles) > 2
        delta = angles[1] - angles[0]
        # make sure angles are spaced correctly
        assert np.isclose(
            np.arange(angles[0], angles[-1]+delta/2., delta),
            np.array(angles)
            ).all()
        self.angles = angles # in degrees
        printf_pattern_candidates = [
            "*CT*_%07.3f_*.fits",
            "*CT*_%.3f_*.fits",
            ]
        found = None
        for c in printf_pattern_candidates:
            from .ImageFileSeries import ImageFileSeries
            c = os.path.join(self.path, c)
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
            if os.path.exists(c):
                found = c; break
            continue
        if not found:
            # fall back is no subdir
            found = '.'
        setattr(self, '%s_subdir' % kind, found)
        candidates = filenamepattern_candidates
        found = None
        for c in candidates:
            pattern = os.path.join(self.path, self.OB_subdir, c)
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
