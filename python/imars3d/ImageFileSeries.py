import os, sys, numpy as np, glob
from .ImageFile import ImageFile


from .AbstractImageSeries import AbstractImageSeries as base
class ImageFileSeries(base):

    """Represent a series of image files. 
    For example, a series of cif files or a series of tiff files.
    """
    
    
    def __init__(self, filename_template, 
                 identifiers=None, decimal_mark_replacement="_", mode="r", name=None):
        """
        filename_template: examples 2014*_CT*_%07.3f_*.fits
        identifiers: a list of identifiers for images
        decimal_mark_replacement: in filenames, the "." decimal mark usually is replaced by a different symbol, often the underscore.
        mode: r or w
        """
        self._init(filename_template, identifiers, decimal_mark_replacement, mode, name)
        return


    def __getstate__(self):
        return dict(
            name = self.name,
            mode = self.mode,
            filename_template = self.filename_template,
            identifiers = self.identifiers,
            decimal_mark_replacement = self.decimal_mark_replacement
            )


    def __setstate__(self, state):
        return self._init(**state)


    def _init(self, filename_template=None,
              identifiers=None, decimal_mark_replacement="_", mode="r", name=None):
        """
        filename_template: examples 2014*_CT*_%07.3f_*.fits
        identifiers: a list of identifiers for images
        decimal_mark_replacement: in filenames, the "." decimal mark usually is replaced by a different symbol, often the underscore.
        mode: r or w
        """
        if mode not in 'rw':
            raise ValueError("Invalid mode: %s" % mode)
        if identifiers is None:
            identifiers = []
        base.__init__(self, mode=mode, identifiers=identifiers, name=name)
        
        self.filename_template = filename_template
        self.decimal_mark_replacement = decimal_mark_replacement
        return

    
    def getslice(self, s):
        return self.__class__(
            self.filename_template, self.identifiers[s],
            self.decimal_mark_replacement, self.mode, self.name)

    
    def getImage(self, identifier):
        p = self.getFilename(identifier)
        return ImageFile(p)
    
        
    def getFilename(self, identifier):
        path_pattern = self._getPathpattern(identifier)
        # don't need to check if file exists if we are creating it
        if self.mode == 'w':
            return path_pattern
        # check if file exists. this is good when reading
        # original data files from the data acqusition system
        # where file name convention is unknown
        paths = glob.glob(path_pattern)
        if len(paths)==0:
            raise RuntimeError("template %r no good: \npath_pattern=%r\npaths=%s" % (
                self.filename_template, path_pattern, paths))
        elif len(paths) > 1:
            pathlist = '\n'.join(paths)
            msg = "\ntemplate %r (path_pattern=%s) found multiple files for %s:\n%s\n" % (
                self.filename_template, path_pattern, identifier, pathlist)
            import warnings
            warnings.warn(msg)
    
        path = paths[0]
        return path
    
    
    def exists(self, identifier):
        assert self.mode == 'w'
        p = self._getPathpattern(identifier)
        return os.path.exists(p)


    def putImage(self, identifier, data):
        p = self._getPathpattern(identifier)
        img = ImageFile(p)
        img.data = data
        img.save()
        return


    def removeAll(self):
        """remove all image files"""
        for identifier in self.identifiers:
            p = self.getFilename(identifier)
            if os.path.exists(p):
                os.remove(p)
            continue
        return


    def _getPathpattern(self, identifier):
        path_pattern = self.filename_template % (identifier,)
        dir = os.path.dirname(path_pattern)
        basename = os.path.basename(path_pattern)
        base, ext = os.path.splitext(basename)
        # bad code
        path_pattern = os.path.join(
            dir, base.replace(".", self.decimal_mark_replacement) + ext)
        return path_pattern
    
    

def imageCollection(glob_pattern, name=None):
    """create an ImageFileSeries instance from a collection of image files
    
    This is intended for a bunch of images that cannot otherwise be identified.
    This is useful for, for example, dark field images and open beam images,
    which really do not need individual access but rather a way to iterate
    over all images in the collection.

    * glob_pattern: glob pattern for image filenames

    """
    import glob
    files = glob.glob(glob_pattern)
    return ImageFileSeries("%s", files, decimal_mark_replacement=".", mode='r', name=name)
