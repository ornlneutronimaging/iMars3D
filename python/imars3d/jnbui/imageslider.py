
from ipywe.imageslider import ImageSlider as base

class ImageSlider(base):

    def __init__(self, name, series, width, height):
        self.name = name
        super(ImageSlider, self).__init__(series, width, height)
        return

    def show(self):
        # for backward compatibility
        return self
