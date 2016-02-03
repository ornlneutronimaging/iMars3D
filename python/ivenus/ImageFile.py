import os, sys, numpy as np, glob


from .AbstractImage import AbstractImage
class ImageFile(AbstractImage):

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

    from astropy.io import fits
    
    @classmethod
    def load(cls, path):
        f = cls.fits.open(path)
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
        
    @classmethod
    def load(cls, path):
        import numpy as np
        return np.load(path)
