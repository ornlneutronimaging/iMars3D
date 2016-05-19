import numpy as np


class FixDeadPixels(object):
    
    def __init__(self, detector_data=None):
        if detector_data is None:
            raise ValueError
        self.detector_data = detector_data

    def fix_xead_pixels(self, **kwargs):
        '''
        This select the right algorithms to fill the dead pixels
        '''
        fill_method = kwargs['fill_method']
        if fill_method == 'mean':
            self.fill_with_mean_value(**kwargs)
        else:
            raise NotImplementedError
        
    def fill_with_mean_value(self, **kwargs):
        pass
   
