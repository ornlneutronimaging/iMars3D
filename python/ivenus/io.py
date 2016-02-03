import os, sys, numpy as np, glob


class ImageSeries:
    
    
    def __init__(self, filename_template, indices, decimal_mark_replacement="_"):
        """
        filename_template: examples 2014*_CT*_%07.3f_*.fits
        indices: a list of indices for images
        decimal_mark_replacement: in filenames, the "." decimal mark usually is replaced by a different symbol, often the underscore.
        """
        self.filename_template = filename_template
        self.indices = indices
        self.decimal_mark_replacement = decimal_mark_replacement
        return

    
    def getImageFile(self, index, **kwds):
        p = self.getFilename(index, **kwds)
        return ImageFile(p)
    
        
    def getFilename(self, index, check_if_exists=True):
        path_pattern = self.filename_template % (index,)
        dir = os.path.dirname(path_pattern)
        basename = os.path.basename(path_pattern)
        base, ext = os.path.splitext(basename)
        # bad code
        path_pattern = os.path.join(
            dir, base.replace(".", self.decimal_mark_replacement) + ext)
        # don't need to check if file exists if we are creating it
        if not check_if_exists:
            return path_pattern
        # check if file exists. this is good when reading
        # original data files from the data acqusition system
        # where file name convention is unknown
        paths = glob.glob(path_pattern)
        if len(paths)!=1:
            raise RuntimeError("template %r no good: \npath_pattern=%r\npaths=%s" % (
                self.filename_template, path_pattern, paths))
    
        path = paths[0]
        return path
    
    
    def getData(self, index):
        path = self.getFilename(index)
        return ImageFile(path).getData()

