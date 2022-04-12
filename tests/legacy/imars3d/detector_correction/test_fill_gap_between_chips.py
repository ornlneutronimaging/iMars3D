#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

from imars3d import detector_correction


def test_fill_gap_with_interpolation():
    chip1 = np.ones((2,2))
    chip2 = np.ones((2,2)) * 2
    chip3 = np.ones((2,2)) * 3
    chip4 = np.ones((2,2)) * 4

    # new detector will be 1 pixel taller and 2 pixels wider
    install_chips_in_new_detector = detector_correction.install_chips_in_new_detector.InstallChipsInNewDetector(new_detector_height = 5,
                                                                                                                new_detector_width = 6)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip1, y_position = 0, x_position = 0)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip2, y_position = 0, x_position = 4)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip3, y_position = 3, x_position = 0)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip4, y_position = 3, x_position = 4)
    new_detector = install_chips_in_new_detector.new_detector
    
    expected_new_detector = np.zeros((5,6))
    expected_new_detector[0:2,0:2] = 1
    expected_new_detector[3:5,0:2] = 3
    expected_new_detector[0:2,4:6] = 2
    expected_new_detector[3:5,4:6] = 4
    
    fill_gap = detector_correction.fill_gap_between_chips.FillGapBetweenChips(detector_data = new_detector)
    fill_gap.correct_gap( fill_method = 'interpolation_x_axis',
                          width_range = [2, 3],
                          height_range = [0, 2])
    expected_new_detector[0:2, 2] = 1.33333333
    expected_new_detector[0:2, 3] = 1.666666667
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    fill_gap.correct_gap( fill_method = 'interpolation_x_axis',
                          width_range = [2, 3],
                          height_range = [3, 5])
    expected_new_detector[3:5, 2] = 3.33333333
    expected_new_detector[3:5, 3] = 3.666666667
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    
    fill_gap.correct_gap( fill_method = 'interpolation_y_axis',
                          width_range = [0, 3],
                          height_range = [2, 2])
    expected_new_detector[2, 0:2] = 2
    expected_new_detector[2, 2] = 2.33333333
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    fill_gap.correct_gap( fill_method = 'interpolation_y_axis',
                          width_range = [3, 6],
                          height_range = [2, 2])
    expected_new_detector[2, 4:6] = 3
    expected_new_detector[2, 3] = 2.666666667
    assert np.allclose(expected_new_detector, fill_gap.detector_data)


def test_fill_gap_with_mean():
    chip1 = np.ones((2,2))
    chip2 = np.ones((2,2)) * 2
    chip3 = np.ones((2,2)) * 3
    chip4 = np.ones((2,2)) * 4

    # new detector will be 1 pixel taller and 2 pixels wider
    install_chips_in_new_detector = detector_correction.install_chips_in_new_detector.InstallChipsInNewDetector(new_detector_height = 5,
                                                                                                                new_detector_width = 6)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip1, y_position = 0, x_position = 0)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip2, y_position = 0, x_position = 4)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip3, y_position = 3, x_position = 0)
    install_chips_in_new_detector.put_chip_in_place(chip_data = chip4, y_position = 3, x_position = 4)
    new_detector = install_chips_in_new_detector.new_detector
    
    expected_new_detector = np.zeros((5,6))
    expected_new_detector[0:2,0:2] = 1
    expected_new_detector[3:5,0:2] = 3
    expected_new_detector[0:2,4:6] = 2
    expected_new_detector[3:5,4:6] = 4
    
    fill_gap = detector_correction.fill_gap_between_chips.FillGapBetweenChips(detector_data = new_detector)
    fill_gap.correct_gap( fill_method = 'mean_x_axis',
                          width_range = [2, 3],
                          height_range = [0, 2])
    expected_new_detector[0:2, 2] = 1.5
    expected_new_detector[0:2, 3] = 1.5
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    fill_gap.correct_gap( fill_method = 'mean_x_axis',
                          width_range = [2, 3],
                          height_range = [3, 5])
    expected_new_detector[3:5, 2] = 3.5
    expected_new_detector[3:5, 3] = 3.5
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    
    fill_gap.correct_gap( fill_method = 'mean_y_axis',
                          width_range = [0, 3],
                          height_range = [2, 2])
    expected_new_detector[2, 0:2] = 2
    expected_new_detector[2, 2] = 2.5
    assert np.allclose(expected_new_detector, fill_gap.detector_data)

    fill_gap.correct_gap( fill_method = 'mean_y_axis',
                          width_range = [3, 6],
                          height_range = [2, 2])
    expected_new_detector[2, 4:6] = 3
    expected_new_detector[2, 3] = 2.5
    assert np.allclose(expected_new_detector, fill_gap.detector_data)


def main():
    test_fill_gap_with_interpolation()
    test_fill_gap_with_mean()
    return


if __name__ == '__main__':
    main()