# interface for Image data object

class AbstractImage:

    def getData(self):
        raise NotImplementedError
        
        
    def save(self):
        raise NotImplementedError
