import os
import numpy as np
import matplotlib.pyplot as plt

from imars3d import config, io
from imars3d import detector_correction


file = "./tests/iMars3D_data_set/Low_res_Gdmask_r0000.fits"
# print('Does file exist: %s' %os.path.isfile(file))

# retrieve image
image_data = io.ImageFile(file).getData()

# plt.figure(1)
# plt.title("Before")
# plt.imshow(image_data, cmap='gray')
# plt.colorbar()
# plt.show()

(detector_width, detector_height) = image_data.shape
chip_width = int(detector_width / 2)
chip_height = int(detector_height / 2)

# isolate chips data
chip1 = image_data[0:chip_height, 0:chip_width]
chip2 = image_data[0:chip_height, chip_width:detector_width]
chip3 = image_data[chip_height:detector_height, 0:chip_width]
chip4 = image_data[chip_height:detector_height, chip_width:detector_width]

# init final image
detector_config = "./python/imars3d/config/detector_dead_pixels.yml"

# retrieve dead pixel values
dead_pixels = detector_correction.retrieve_mcp_dead_pixels.RetrieveMCPDeadPixels(detector_config)


print(dead_pixels.mode.low_resolution["group1"])


# print(dead_pixels.low_resolution)
# fix_dead_pixels = detector_correction.fix_dead_pixels.FixDeadPixels(detector_data = image_data)
