import os, sys, numpy as np, pylab, glob


class ImageSeries:
    
    
    def __init__(self, filename_template, angles):
        self.filename_template = filename_template
        self.angles = angles
        return

    
    def getImageFile(self, angle):
        p = self.getFilename(angle)
        return ImageFile(p)
    
        
    def getFilename(self, angle):
        path_pattern = self.filename_template % (angle,)
        dir = os.path.dirname(path_pattern)
        basename = os.path.basename(path_pattern)
        base, ext = os.path.splitext(basename)
        # bad code
        path_pattern = os.path.join(dir, base.replace(".", "_") + ext)
        
        paths = glob.glob(path_pattern)
        if len(paths)!=1:
            raise RuntimeError, "template %r no good: \npath_pattern=%r" % (
                self.filename_template, path_pattern)
    
        path = paths[0]
        return path
    
    
    def getData(self, angle):
        path = self.getFilename(angle)
        return ImageFile(path).getData()


class ImageFile:

    def __init__(self, path):
        self.path = path
        return


    def getData(self):
        io = self._getIO()
        return io.load(self.path)
        
        
    def save(self):
        io = self._getIO()
        io.dump(self.data, self.path)
        return
        

    def _getIO(self):
        fn, ext = os.path.splitext(self.path)
        return eval(ext[1:].capitalize() + "ImageIO")


class AbstractImageFileIO:
    
    @classmethod
    def load(cls, path): raise NotImplementedError
    
    @classmethod
    def dump(cls, data, path): raise NotImplementedError


class FitsImageIO:
    
    @classmethod
    def load(cls, path):
        from astropy.io import fits
        f = fits.open(path)
        d = f[0].data
        f.close()
        return d


class NpyImageIO:

    @classmethod
    def dump(cls, data, path):
        import numpy as np
        np.save(path, data)
        return
