# interface for image series

class AbstractImageSeries:

    
    def __init__(self, mode=None, identifiers=None):
        """mode: read (r) or write (w)
        identifiers: a list of identifiers, each identifies one image in the series
        """
        self.mode = mode
        self.identifiers = identifiers
        return
    
    
    def getImage(self, index):
        "return an image instance"
        raise NotImplementedError
    
        
    def getData(self, index):
        "return a numpy array of the image data"
        img = self.getImage(index)
        return img.getData()

