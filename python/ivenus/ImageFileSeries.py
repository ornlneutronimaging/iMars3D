import os, sys, numpy as np, glob


from .AbstractImageSeries import AbstractImageSeries as base
class ImageFileSeries(base):

    """Represent a series of image files. 
    For example, a series of cif files or a series of tiff files.
    """
    
    
    def __init__(self, filename_template, identifiers, decimal_mark_replacement="_", mode="r"):
        """
        filename_template: examples 2014*_CT*_%07.3f_*.fits
        identifiers: a list of identifiers for images
        decimal_mark_replacement: in filenames, the "." decimal mark usually is replaced by a different symbol, often the underscore.
        mode: r or w
        """
        if mode not in 'rw':
            raise ValueError("Invalid mode: %s" % mode)
        base.__init__(self, mode, identifiers)
        
        self.filename_template = filename_template
        self.decimal_mark_replacement = decimal_mark_replacement
        return

    
    def getImage(self, identifier):
        from .ImageFile import ImageFile
        p = self.getFilename(identifier)
        return ImageFile(p)
    
        
    def getFilename(self, identifier):
        path_pattern = self.filename_template % (identifier,)
        dir = os.path.dirname(path_pattern)
        basename = os.path.basename(path_pattern)
        base, ext = os.path.splitext(basename)
        # bad code
        path_pattern = os.path.join(
            dir, base.replace(".", self.decimal_mark_replacement) + ext)
        # don't need to check if file exists if we are creating it
        if self.mode == 'w':
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
    

def imageCollection(glob_pattern):
    """create an ImageFileSeries instance from a collection of image files
    
    This is intended for a bunch of images that cannot otherwise be identified.
    This is useful for, for example, dark field images and open beam images,
    which really do not need individual access but rather a way to iterate
    over all images in the collection.

    * glob_pattern: glob pattern for image filenames

    """
    import glob
    files = glob.glob(glob_pattern)
    return ImageFileSeries("%s", files, decimal_mark_replacement=".", mode='r')
