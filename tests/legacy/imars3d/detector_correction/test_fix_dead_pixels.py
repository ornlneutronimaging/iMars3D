#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

from imars3d import detector_correction

thisdir = os.path.dirname(__file__)

def test_retrieving_low_and_high_resolution_dead_pixels():
    
    # init final image
    detector_config = os.path.join(thisdir, '../../../python/imars3d/config/detector_dead_pixels.yml')
    
    # retrieve dead pixel values
    dead_pixels = detector_correction.retrieve_mcp_dead_pixels.RetrieveMCPDeadPixels(detector_config)
    
    
    # low resolution
    top_pixel = dead_pixels.mode.low_resolution['group1'].top
    expected_top_pixel = 195
    assert expected_top_pixel == top_pixel
    
    bottom_pixel = dead_pixels.mode.low_resolution['group1'].bottom
    expected_bottom_pixel = 200
    assert expected_bottom_pixel == bottom_pixel
    
    left_pixel = dead_pixels.mode.low_resolution['group1'].left
    expected_left_pixel = 190
    assert expected_left_pixel == left_pixel

    right_pixel = dead_pixels.mode.low_resolution['group1'].right
    expected_right_pixel = 194
    assert expected_right_pixel == right_pixel

    
    # high resolution
    top_pixel = dead_pixels.mode.high_resolution['group1'].top
    expected_top_pixel = 1598
    assert expected_top_pixel == top_pixel
    
    bottom_pixel = dead_pixels.mode.high_resolution['group1'].bottom
    expected_bottom_pixel = 2579
    assert expected_bottom_pixel == bottom_pixel
    
    left_pixel = dead_pixels.mode.high_resolution['group1'].left
    expected_left_pixel = 1555
    assert expected_left_pixel == left_pixel
    

    right_pixel = dead_pixels.mode.high_resolution['group1'].right
    expected_right_pixel = 2535
    assert expected_right_pixel == right_pixel



def main():
    test_retrieving_low_and_high_resolution_dead_pixels()
    return


if __name__ == '__main__':
    main()
