# interface for image series

class AbstractImageSeries:

    
    def __init__(self, mode=None, identifiers=None, name=None):
        """mode: read (r) or write (w)
        identifiers: a list of identifiers, each identifies one image in the series
        """
        self.mode = mode
        self.identifiers = identifiers
        self.nImages = len(identifiers)
        self.name = name
        return
        
        
    def __getitem__(self, i):
        return self.getImage(self.identifiers[i])

    def __iter__(self):
        return ImageIterator(self)

    def __len__(self):
        return len(self.identifiers)


    def iterImages(self):
        for identifier in self.identifiers:
            yield self.getImage(identifier)
        return

    
    def getImage(self, identifier):
        "return an image instance"
        raise NotImplementedError


    def getData(self, identifier):
        "return a numpy array of the image data"
        img = self.getImage(identifier)
        return img.getData()


    def exists(self, identifier):
        "check whether an image exists"
        raise NotImplementedError
    
        
    def putImage(self, identifier, data):
        "write image data for one image identified by the identifier"
        raise NotImplementedError


class ImageIterator():

    def __init__(self, imgseries):
        self.imgseries = imgseries
        self.index = 0
        return

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.imgseries):
            raise StopIteration
        r = self.imgseries[self.index]
        self.index +=1
        return r
