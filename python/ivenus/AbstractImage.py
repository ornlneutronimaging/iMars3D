# interface for Image data object

class AbstractImage:

    # data should be a property of an image instance.
    # set this to a npy array before the save method is called
    data = None 

    def getData(self):
        raise NotImplementedError
        
        
    def save(self):
        raise NotImplementedError
