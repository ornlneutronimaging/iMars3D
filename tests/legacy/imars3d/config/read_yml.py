#!/usr/bin/env python

from imars3d import config

# the goal of this function is to play with the yaml reader
# and learn how to retrieve values from the config file

# read a yml file and convert it into python object
detector_offset_filename = "./detector_offset.yml"
detector_config = config.loadYmlConfig(detector_offset_filename)

chips_offset = detector_config.detector.chips
print("chip1: position: top: %s" % chips_offset.chip1.position.top)
