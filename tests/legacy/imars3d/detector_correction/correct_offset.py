import os
import numpy as np
import matplotlib.pyplot as plt

from imars3d import config, io
from imars3d import detector_correction


file = './tests/iMars3D_data_set/Low_res_Gdmask_r0000.fits'
#print('Does file exist: %s' %os.path.isfile(file))

# retrieve image
image_data = io.ImageFile(file).getData()

#plt.figure(1)
#plt.title("Before")
#plt.imshow(image_data, cmap='gray')
#plt.colorbar()
#plt.show()

(detector_width, detector_height) = image_data.shape
chip_width = int(detector_width/2)
chip_height = int(detector_height/2)

# isolate chips data
chip1 = image_data[0:chip_height, 0:chip_width]
chip2 = image_data[0:chip_height, chip_width:detector_width]
chip3 = image_data[chip_height:detector_height, 0:chip_width]
chip4 = image_data[chip_height:detector_height, chip_width:detector_width]

# init final image
detector_config = './python/imars3d/config/detector_offset.yml'

# retrieve offset values
chips_offset = detector_correction.retrieve_mcp_chips_offset.RetrieveMCPChipsOffset(detector_config)

## calculate max x and y offset (to determine size of new image)
new_detector_width_offset = chips_offset.get_detector_new_width_offset()
#print('new_detector_width_offset: %d' %new_detector_width_offset)
new_detector_height_offset = chips_offset.get_detector_new_height_offset()
#print('new_detector_height_offset: %d' %new_detector_height_offset)

new_detector_width = detector_width + new_detector_width_offset
new_detector_height = detector_height + new_detector_height_offset

install_chips_in_new_detector = detector_correction.install_chips_in_new_detector.InstallChipsInNewDetector(new_detector_height = new_detector_height,
                                                                                                            new_detector_width = new_detector_width)
install_chips_in_new_detector.put_chip_in_place(chip_data = chip1, y_position = 0, x_position = 0)

chip2_offset = chips_offset.chips.chip2
install_chips_in_new_detector.put_chip_in_place(chip_data = chip2, 
                                                y_position = chip2_offset.y_offset, 
                                                x_position = chip2_offset.x_offset + chip_width)


chip3_offset = chips_offset.chips.chip3
install_chips_in_new_detector.put_chip_in_place(chip_data = chip3, 
                                                y_position = chip3_offset.y_offset + chip_height, 
                                                x_position = chip3_offset.x_offset)


chip4_offset = chips_offset.chips.chip4
install_chips_in_new_detector.put_chip_in_place(chip_data = chip4, 
                                                y_position = chip4_offset.y_offset + chip_height, 
                                                x_position = chip4_offset.x_offset + chip_width)

# retrieve new detector
new_detector = install_chips_in_new_detector.new_detector

#plt.figure(2)
#plt.title("After")
#plt.imshow(new_detector, cmap='gray')
#plt.colorbar()
#plt.show()

# correct gap by using linear interpolation
fill_gap = detector_correction.fill_gap_between_chips.FillGapBetweenChips(detector_data = new_detector)

method = 'mean'

if method == 'interpolation':


    # top and bottom vertical strips
    fill_gap.correct_gap( fill_method = 'interpolation_x_axis',
                          width_range = [chip_width, chip_width + chip2_offset.x_offset],
                          height_range = [chip2_offset.y_offset, chip_height])
    fill_gap.correct_gap( fill_method = 'interpolation_x_axis',
                          width_range = [chip3_offset.x_offset + chip_width, 
                                         chip3_offset.x_offset + chip_width + chip4_offset.x_offset],
                          height_range = [chip4_offset.y_offset + chip_height, 
                                          2*chip_height + chip4_offset.y_offset])
    
    # horizontal strips
    fill_gap.correct_gap( fill_method = 'interpolation_y_axis',
                          width_range = [chip3_offset.x_offset, chip_width + chip3_offset.x_offset],
                          height_range = [chip_height, chip_height + chip3_offset.y_offset])
    fill_gap.correct_gap( fill_method = 'interpolation_y_axis',
                          width_range = [chip4_offset.x_offset + chip_width, chip4_offset.x_offset + 2*chip_width],
                          height_range = [chip2_offset.y_offset + chip_height, chip_height + chip4_offset.y_offset])
    
    # center of detector
    fill_gap.correct_gap( fill_method = 'interpolation_x_axis',
                          width_range = [chip_width, chip_width + max(chip2_offset.x_offset, chip4_offset.x_offset)],
                          height_range = [chip_height, chip_height + max(chip3_offset.y_offset, chip4_offset.y_offset)])

elif method == 'mean':
    
    # top and bottom vertical strips
    fill_gap.correct_gap( fill_method = 'mean_x_axis',
                          width_range = [chip_width, chip_width + chip2_offset.x_offset],
                          height_range = [chip2_offset.y_offset, chip_height])    
    fill_gap.correct_gap( fill_method = 'mean_x_axis',
                          width_range = [chip3_offset.x_offset + chip_width, 
                                         chip3_offset.x_offset + chip_width + chip4_offset.x_offset],
                          height_range = [chip4_offset.y_offset + chip_height, 
                                          2*chip_height + chip4_offset.y_offset])

    # horizontal strips
    fill_gap.correct_gap( fill_method = 'mean_y_axis',
                          width_range = [chip3_offset.x_offset, chip_width + chip3_offset.x_offset],
                          height_range = [chip_height, chip_height + chip3_offset.y_offset])
    fill_gap.correct_gap( fill_method = 'mean_y_axis',
                          width_range = [chip4_offset.x_offset + chip_width, chip4_offset.x_offset + 2*chip_width],
                          height_range = [chip2_offset.y_offset + chip_height, chip_height + chip4_offset.y_offset])


    # center of detector
    fill_gap.correct_gap( fill_method = 'mean_x_axis',
                          width_range = [chip_width, chip_width + max(chip2_offset.x_offset, chip4_offset.x_offset)],
                          height_range = [chip_height, chip_height + max(chip3_offset.y_offset, chip4_offset.y_offset)])


plt.figure(3)
plt.title("After")
plt.imshow(fill_gap.detector_data, cmap='gray')
plt.colorbar()
plt.show()


