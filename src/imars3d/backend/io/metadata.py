#!/usr/bin/env python3
"""
Metadata class for IMars3D
"""
import numpy as np
import param
import tifffile
from pathlib import Path


# setup module level logger
logger = param.get_logger(__name__)
logger.name = __name__


class MetaData(param.Parameterized):
    """
    Metadata extracted from given file
    """

    filename = param.Filename(doc="full path to the file.")
    datatype = param.Selector(
        default="ct",
        objects=[
            "radiograph",
            "ct",
            "openbeam",
            "ob",
            "darkcurrent",
            "dc",
        ],
        doc="data type [ct|ob|dc]",
    )
    metadata_index = param.List(
        default=[
            65026,  # "ManufacturerStr:Andor"
            65027,  # "ExposureTime:70.000000"
            65068,  # "MotSlitHR.RBV:10.000000"
            65070,  # "MotSlitHL.RBV:20.000000"
            65066,  # "MotSlitVT.RBV:10.000000"
            65068,  # "MotSlitHR.RBV:10.000000"
        ],
        doc="list of metadata keys to be extracted from the file.",
    )
    metadata = param.Dict(
        default={},
        doc="dictionary of metadata extracted from the file.",
    )
    relative_tolerance = param.Number(
        default=0.01,
        doc="relative tolerance for comparing metadata values.",
    )

    @property
    def suffix(self) -> str:
        return Path(self.filename).suffix

    @param.depends("filename", "datatype", watch=True, on_init=True)
    def _update_metadata_index(self):
        """
        Update metadata index
        """
        if self.suffix.lower() in (".tiff", "tif"):
            # NOTE: trim slits position from metadata_keys if the file is
            #       dark current file
            if self.datatype in ("darkcurrent", "dc"):
                self.metadata_index = [65026, 65027]
        elif self.suffix.lower() in (".fits", ".fit"):
            raise ValueError(f'Suffix="{self.suffix}" is not currently supported')

    @param.depends("filename", "metadata_index", watch=True, on_init=True)
    def _update_metadata(self):
        if self.suffix.lower() in (".tiff", "tif"):
            self.metadata = _extract_metadata_from_tiff(self.filename, self.metadata_index)
        elif self.suffix.lower() in (".fits", ".fit"):
            raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, MetaData):
            raise NotImplementedError
        # find the most common keys
        common_keys = [k for k in self.metadata.keys() if k in other.metadata.keys()]
        # check all entries
        is_match = True
        for k in common_keys:
            me = self.metadata[k]
            te = other.metadata[k]
            if isinstance(me, str):
                is_match = me == te
            elif isinstance(me, float):
                is_match = (np.isclose(me, te, rtol=self.relative_tolerance))
            # break early if is_match if false
            if not is_match:
                break
        return is_match

    def match(self, other_filename: str, other_datatype: str) -> bool:
        # instantiate metadata for other file
        other = MetaData(filename=other_filename, datatype=other_datatype)
        return self == other


def _extract_metadata_from_tiff(
    filename: str,
    index: list[int],
) -> dict:
    """
    Extract metadata from tiff file.

    Parameters
    ----------
    filename :
        full path to the tiff file.
    index :
        list of metadata keys/index to be extracted from tiff tags.

    Returns
    -------
    metadata :
        dictionary of metadata extracted from the tiff file.
    """
    tiff = tifffile.TiffFile(filename)
    metadata = dict([tiff.pages[0].tags[i].value.split(":") for i in index])
    # map to correct type
    for k, v in metadata.items():
        try:
            v = float(v)
        except ValueError:
            pass
        metadata[k] = v
    return metadata
