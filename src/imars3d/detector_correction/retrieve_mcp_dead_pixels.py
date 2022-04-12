from imars3d.config import *


class Mode(object):
    """
    object class that just keep record of the mode (low_res and high_res)
    """

    low_resolution = []
    high_resolution = []


class GroupRegion(object):
    """
    define group region
    """

    top = 0
    bottom = 0
    left = 0
    right = 0

    def __repr__(self):
        top = "Top: %d" % self.top
        bottom = "Bottom: %d" % self.bottom
        left = "Left: %d" % self.left
        right = "Right: %d" % self.right
        return "%s\n%s\n%s\n%s" % (top, bottom, left, right)


class RetrieveMCPDeadPixels(object):
    """
    Using the yml file given as parameters, this class
    will retrieve the MCP dead pixels regions
    """

    config_file_name = ""
    mode = None

    def __init__(self, config_file_name):
        self.config_file_name = config_file_name
        self.retrieve_all_regions()

    def retrieve_all_regions(self):
        """
        retrieve from the yml file the various dead pixels region
        """
        detector_config = loadYmlConfig(self.config_file_name)
        modes = detector_config.detector.mode

        self.mode = Mode()

        self.mode.low_resolution = modes["low_resolution"].__dict__
        self.mode.high_resolution = modes["high_resolution"].__dict__
