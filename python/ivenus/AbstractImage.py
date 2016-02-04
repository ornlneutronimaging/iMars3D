# interface for Image data object

class AbstractImage:

    @property
    def data(self):
        if not hasattr(self, "_data"):
            self._data = self.getData()
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @data.deleter
    def data(self):
        del self._data


    def getData(self):
        raise NotImplementedError
        
        
    def save(self):
        raise NotImplementedError
