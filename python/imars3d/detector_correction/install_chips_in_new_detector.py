import numpy as np



class InstallChipsInNewDetector(object):
    
    new_detector = None

    def __init__(self, new_detector_height = 0,
                 new_detector_width = 0):
        
        self.new_detector_height = new_detector_height
        self.new_detector_width = new_detector_width
        
        self.init_new_detector()
        
    def init_new_detector(self):
        
        self.new_detector = np.zeros((self.new_detector_height, 
                                      self.new_detector_width))
        
    def put_chip_in_place(self, chip_data=None, y_position=0, x_position=0):
        [chip_height, chip_width] = chip_data.shape
        self.new_detector[y_position : y_position + chip_height, 
                          x_position : x_position + chip_width] = chip_data