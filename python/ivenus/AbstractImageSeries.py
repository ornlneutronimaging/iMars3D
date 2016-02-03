# interface for image series

class AbstractImageSeries:

    
    def __init__(self, mode=None, identifiers=None):
        """mode: read (r) or write (w)
        identifiers: a list of identifiers, each identifies one image in the series
        """
        self.mode = mode
        self.identifiers = identifiers
        self.nImages = len(identifiers)
        return


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

