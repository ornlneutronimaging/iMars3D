import numpy as np


class FillGapBetweenChips(object):
    '''
    This class takes a 2D detector data and will fill the gap in the pixel range according to the
    interpolation direction defined
    
    * fill_methods: 
       - interpolation_x_axis
       - interpolation_y_axis
       - copy_bottom_edge
       - copy_top_edge
       - copy_left_edge
       - copy_right_edge
    
    '''
    
    def __init__(self, detector_data=None):
        if detector_data is None:
            raise ValueError
        self.detector_data = detector_data

        
    def correct_gap(self, **kwargs):
        '''This select the right algorithm to use for the right gap
        
        if the gap is along the x_axis, it will interpolate along this axis, etc.
        
        '''
        fill_method = kwargs['fill_method'] 
        if fill_method ==  'interpolation_x_axis':
            self.interpolation_x_axis(**kwargs)
        elif fill_method == 'interpolation_y_axis':
            self.interpolation_y_axis(**kwargs)
        elif fill_method == 'mean_x_axis':
            self.mean_x_axis(**kwargs)
        elif fill_method == 'mean_y_axis':
            self.mean_y_axis(**kwargs)
            

    def mean_x_axis(self, **kwargs):
        [from_x, to_x] = kwargs['width_range']
        [from_y, to_y] = kwargs['height_range']
        
        _detector_data = self.detector_data
        
        for y in np.arange(from_y, to_y):
            left_value = _detector_data[y, from_x-1]
            right_value = _detector_data[y, to_x+1]
            
            gap_values = np.ones(to_x  - (from_x-1)) * np.mean([left_value, right_value])
            _detector_data[y, from_x: to_x+1] = gap_values

        self.detector_data = _detector_data


    def mean_y_axis(self, **kwargs):
        [from_x, to_x] = kwargs['width_range']
        [from_y, to_y] = kwargs['height_range']
        
        _detector_data = self.detector_data
        
        for x in np.arange(from_x, to_x):
            top_value = _detector_data[from_y-1, x]
            bottom_value = _detector_data[to_y+1, x]
            
            gap_values = np.ones(to_y  - (from_y-1)) * np.mean([top_value, bottom_value])
            _detector_data[from_y: to_y+1, x] = gap_values

        self.detector_data = _detector_data


    def interpolation_x_axis(self, **kwargs):
        [from_x, to_x] = kwargs['width_range']
        [from_y, to_y] = kwargs['height_range']
        
        _detector_data = self.detector_data
        
        for y in np.arange(from_y, to_y):
            left_value = _detector_data[y, from_x-1]
            right_value = _detector_data[y, to_x+1]
            
            missing_point = np.arange(from_x, to_x + 1)
            gap_values = np.interp(missing_point, [from_x-1, to_x+1], [left_value, right_value])
                                   
            _detector_data[y, from_x: to_x+1] = gap_values

        self.detector_data = _detector_data
        
        
    def interpolation_y_axis(self, **kwargs):
        [from_x, to_x] = kwargs['width_range']
        [from_y, to_y] = kwargs['height_range']
        
        _detector_data = self.detector_data
        
        for x in np.arange(from_x, to_x):
            top_value = _detector_data[from_y-1, x]
            bottom_value = _detector_data[to_y+1, x]
            
            missing_point = np.arange(from_y, to_y + 1)
            gap_values = np.interp(missing_point, [from_y-1, to_y+1], [top_value, bottom_value])
                                   
            _detector_data[from_y: to_y+1, x] = gap_values

        self.detector_data = _detector_data