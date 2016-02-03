# interface for image series

class AbstractImageSeries:

    
    def __init__(self, mode=None):
        """mode: read (r) or write (w)
        """
        self.mode = mode
        return
    
    
    def getImage(self, index):
        "return an image instance"
        raise NotImplementedError
    
        
    def getData(self, index):
        "return a numpy array of the image data"
        image = self.getImage(index)
        return img.getData()

