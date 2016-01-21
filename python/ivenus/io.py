import os, sys, numpy as np, glob


class ImageSeries:
    
    
    def __init__(self, filename_template, angles, decimal_mark_replacement="_"):
        """
        filename_template: examples 2014*_CT*_%07.3f_*.fits
        angles: a list of angles
        decimal_mark_replacement: in filenames, the "." decimal mark usually is replaced by a different symbol, often the underscore.
        """
        self.filename_template = filename_template
        self.angles = angles
        self.decimal_mark_replacement = decimal_mark_replacement
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
        path_pattern = os.path.join(
            dir, base.replace(".", self.decimal_mark_replacement) + ext)
        
        paths = glob.glob(path_pattern)
        if len(paths)!=1:
            raise RuntimeError("template %r no good: \npath_pattern=%r" % (
                self.filename_template, path_pattern))
    
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


class FitsImageIO(AbstractImageFileIO):
    
    @classmethod
    def load(cls, path):
        from astropy.io import fits
        f = fits.open(path)
        d = f[0].data
        f.close()
        dtype = cls._getDataType(path)
        return np.array(d, dtype=dtype)
    
    
    @classmethod
    def _getDataType(cls, path):
        bitpix = cls._readBITPIX(path)
        if bitpix > 0: dtype = 'uint%s' % bitpix
        else: dtype = 'int%s' % -bitpix
        return dtype
        

    @classmethod
    def _readBITPIX(cls, path):
        # astropy fits reader has a problem
        # have to read BITPIX from the fits file directly
        stream = open(path, 'rb')
        while True:
            line = stream.read(80).decode("utf-8")
            if line.startswith('BITPIX'):
                value = line.split('/')[0].split('=')[1].strip()
                value = int(value)
                break
            continue
        stream.close()
        return value


class NpyImageIO(AbstractImageFileIO):

    @classmethod
    def dump(cls, data, path):
        import numpy as np
        np.save(path, data)
        return
