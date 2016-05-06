# CT data object
# A CT object contains a CT scan and OB and DF images.

import os, glob

class CT:

    def __init__(self, path):
        self.path = path
        return


    def sniff(self):
        self.find_OB()
        self.find_DF()
        self.find_CT()
        return
        
        
    def find_CT(self):
        pattern = '*CT*_*_*.fits'
        files = glob.glob(os.path.join(self.path, pattern))
        import pdb; pdb.set_trace()
        return

    
    def find_OB(self):
        return self._find_pattern(
            subdir_candidates = ['ob', 'OB'],
            filenamepattern_candidates = ['*ob*', '*OB*'],
            )

    def find_DF(self):
        return self._find_pattern(
            subdir_candidates = ['df', 'DF'],
            filenamepattern_candidates = ['*df*', '*DF*'],
            )


    def _find_pattern(self, subdir_candidates, filenamepattern_candidates):
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
        self.OB_subdir = found
        candidates = filenamepattern_candidates
        found = None
        for c in candidates:
            pattern = os.path.join(self.path, self.OB_subdir, c)
            files = glob.glob(pattern)
            if files:
                found = pattern; break
            continue
        self.OB_pattern = found
        return

    pass


# End of file
