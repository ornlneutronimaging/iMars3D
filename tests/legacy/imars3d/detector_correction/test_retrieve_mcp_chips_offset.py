#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

from imars3d import detector_correction


def test_mcp_chips_offset():
    dir = os.path.dirname(__file__)
    datadir = os.path.join(dir, "..", "..", "imars3d", "config")

    # init final image
    detector_config = os.path.join(datadir, "detector_offset.yml")

    # retrieve offset values
    chips_offset = detector_correction.retrieve_mcp_chips_offset.RetrieveMCPChipsOffset(detector_config)

    assert chips_offset.chips.chip1.x_offset == 0
    assert chips_offset.chips.chip1.y_offset == 0

    assert chips_offset.chips.chip2.x_offset == 2
    assert chips_offset.chips.chip2.y_offset == 1

    assert chips_offset.chips.chip3.y_offset == 3
    assert chips_offset.chips.chip3.x_offset == 0

    assert chips_offset.chips.chip4.y_offset == 3
    assert chips_offset.chips.chip4.x_offset == 2


def test_mcp_create_new_detector():
    chip1 = np.ones((2, 2))
    chip2 = np.ones((2, 2)) * 2
    chip3 = np.ones((2, 2)) * 3
    chip4 = np.ones((2, 2)) * 4

    # new detector will be 1 pixel taller and 2 pixels wider
    install_chips_in_new_detector = detector_correction.install_chips_in_new_detector.InstallChipsInNewDetector(
        new_detector_height=5, new_detector_width=6
    )
    install_chips_in_new_detector.put_chip_in_place(chip_data=chip1, y_position=0, x_position=0)
    install_chips_in_new_detector.put_chip_in_place(chip_data=chip2, y_position=0, x_position=4)
    install_chips_in_new_detector.put_chip_in_place(chip_data=chip3, y_position=3, x_position=0)
    install_chips_in_new_detector.put_chip_in_place(chip_data=chip4, y_position=3, x_position=4)
    new_detector = install_chips_in_new_detector.new_detector

    expected_new_detector = np.zeros((5, 6))
    expected_new_detector[0:2, 0:2] = 1
    expected_new_detector[3:5, 0:2] = 3
    expected_new_detector[0:2, 4:6] = 2
    expected_new_detector[3:5, 4:6] = 4

    assert (new_detector == expected_new_detector).all()


def main():
    test_mcp_chips_offset()
    test_mcp_create_new_detector()
    return


if __name__ == "__main__":
    main()
