from imars3d import config



class Chips(object):
    '''
    object class that just keep record of the offset 
    of the various chips
    '''
    chip1 = None
    chip2 = None
    chip3 = None
    chip4 = None
    
class ChipOffset(object):
    '''
    define chip offset 
    '''
    x_offset = 0
    y_offset = 0

class RetrieveMCPChipsOffset(object):
    '''
    Using the yml file given as parameters, this class
    will retrieve the MCP xoffset and yoffset of the 4 various chips
    '''
    
    config_file_name = ''
    chips = None
    
    def __init__(self, config_file_name):
        self.config_file_name = config_file_name
        self.retrieve_all_offset()
        
    def retrieve_all_offset(self):
        '''
        retrieve from the yml file the various xoffset, yoffset of the chips
        '''
        detector_config = config.loadYmlConfig(self.config_file_name)
        chips_offset = detector_config.detector.chips
        
        self.chips = Chips()
        self.chips.chip1 = self.retrieve_chip_offset(chips_offset.chip1)
        self.chips.chip2 = self.retrieve_chip_offset(chips_offset.chip2)
        self.chips.chip3 = self.retrieve_chip_offset(chips_offset.chip3)
        self.chips.chip4 = self.retrieve_chip_offset(chips_offset.chip4)
        
    def retrieve_chip_offset(self, chip):
        '''
        passing the chip # object structure, retrieve the x and y value of the offset
        '''
        _chip = ChipOffset()
        _chip.x_offset = chip.offset.x
        _chip.y_offset = chip.offset.y
        return _chip

    def get_detector_new_width_offset(self):
        chip2_x_offset = self.chips.chip2.x_offset
        chip3_x_offset = self.chips.chip3.x_offset
        chip4_x_offset = self.chips.chip4.x_offset
        
        if chip2_x_offset <= 0:
            if chip4_x_offset <= 0:
                if chip3_x_offset <= 0:
                    return abs(chip3_x_offset)
                else:
                    return 0
            else:
                if chip3_x_offset <= 0:
                    return abs(chip3_x_offset) + abs(chip4_x_offset)
                else:
                    return chip4_x_offset
        else:
            if chip4_x_offset <= 0:
                if chip3_x_offset <= 0:
                    return abs(chip3_x_offset) + abs(chip2_x_offset)
                else:
                    return abs(chip2_x_offset)
            else:
                if chip3_x_offset <= 0:
                    max_offset = max([abs(chip4_x_offset), abs(chip2_x_offset)])
                    return abs(chip3_x_offset) + max_offset
                else:
                    return max[abs(chip4_x_offset), abs(chip2_x_offset)]
                
    def get_detector_new_height_offset(self):
        chip2_y_offset = self.chips.chip2.y_offset
        chip3_y_offset = self.chips.chip3.y_offset
        chip4_y_offset = self.chips.chip4.y_offset
           
        if chip2_y_offset <= 0:
            if chip4_y_offset <= 0:
                if chip3_y_offset <= 0:
                    return abs(chip3_y_offset)
                else:
                    return 0
            else:
                if chip3_y_offset <= 0:
                    return abs(chip3_y_offset) + abs(chip4_y_offset)
                else:
                    return chip4_y_offset
        else:
            if chip4_y_offset <= 0:
                if chip3_y_offset <= 0:
                    return abs(chip3_y_offset) + abs(chip2_y_offset)
                else:
                    return abs(chip2_y_offset)
            else:
                if chip3_y_offset <= 0:
                    max_offset = max([abs(chip4_y_offset), abs(chip2_y_offset)])
                    return abs(chip3_y_offset) + max_offset
                else:
                    return max([abs(chip4_y_offset), abs(chip2_y_offset)])    


    def get_height_offset(self):
        pass
        
    def get_max_offset(self):
        '''
        return a tuple of the max x and y offset
        '''
        max_x_offset = max(self.list_x_offset())
        max_y_offset = max(self.list_y_offset())
        return [max_x_offset, max_y_offset]
        
    def list_x_offset(self):
        list_x_offset  = []
        for name in self.chips.__dict__:
            if name.startswith("_"): continue
            value = getattr(self.chips, name)[0]
            list_x_offset.append(value)
        return list_x_offset
        
    def list_y_offset(self):
        list_y_offset  = []
        for name in self.chips.__dict__:
            if name.startswith("_"): continue
            value = getattr(self.chips, name)[1]
            list_y_offset.append(value)
        return list_y_offset
    
    
