# interface for image series

class AbstractImageSeries:
    
    
    def getImage(self, index, **kwds):
        
    
        
    def getData(self, index):
        path = self.getFilename(index)
        return ImageFile(path).getData()

