#!/usr/bin/env python3
"""
Data handling for imars3d.
"""
import re
import param
import multiprocessing
import numpy as np
import dxchange
import tifffile
from functools import partial
from pathlib import Path
from fnmatch import fnmatchcase
from typing import Optional, Tuple, List, Callable
from tqdm.contrib.concurrent import process_map


# setup module level logger
logger = param.get_logger(__name__)
logger.name = __name__
METADATA_DICT = {
    65026: "ManufacturerStr:Andor",  # [ct, ob, dc]
    65027: "ExposureTime:70.000000",  # [ct, ob, dc]
    65068: "MotSlitHR.RBV:10.000000",  # APERTURE_HR, [ct, ob]
    65070: "MotSlitHL.RBV:20.000000",  # APERTURE_HL, [ct, ob]
    65066: "MotSlitVT.RBV:10.000000",  # APERTURE_VT, [ct, ob]
    65068: "MotSlitHR.RBV:10.000000",  # APERTURE_VB, [ct, ob]
}


class load_data(param.ParameterizedFunction):
    """
    Load data with given input

    Parameters
    ---------
    ct_files: str
        explicit list of radiographs
    ob_files: str
        explicit list of open beams
    dc_files: Optional[str]
        explicit list of dark current
    ct_dir: str
        directory contains radiographs
    ob_dir: str
        directory contains open beams
    dc_dir: Optional[str]
        directory contains dark currents
    ct_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting radiographs
    ob_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting open beams
    dc_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting dark current
    max_workers: Optional[int]
        maximum number of processes allowed during loading, default to use as many as possible.

    Returns
    -------
        radiograph stacks, obs, dcs and omegas as numpy.ndarray

    Notes
    -----
        There are two main signatures to load the data:
        1. load_data(ct_files=ctfs, ob_files=obfs, dc_files=dcfs)
        2. load_data(ct_dir=ctdir, ob_dir=obdir, dc_dir=dcdir)

        The two signatures are mutually exclusive, and dc_files and dc_dir are optional
        in both cases as some experiments do not have dark current measurements.

        The fnmatch selectors are applicable in both signature, which help to down-select
        files if needed. Default is set to "*", which selects everything.
        Also, if ob_fnmatch and dc_fnmatch are set to "None" in the second signature call, the
        data loader will attempt to read the metadata embedded in the ct file to find obs
        and dcs with similar metadata.

        Currently, we are using a forgiving reader to load the image where a corrupted file
        will not block reading other data.
    """

    #
    ct_files = param.List(doc="list of all ct files to load")
    ob_files = param.List(doc="list of all ob files to load")
    dc_files = param.List(doc="list of all dc files to load")
    #
    ct_dir = param.Foldername(doc="radiograph directory")
    ob_dir = param.Foldername(doc="open beam directory")
    dc_dir = param.Foldername(doc="dark current directory")
    # NOTE: we need to provide a default value here as param.String default to "", which will
    #       not trigger dict.get(key, value) to get the value as "" is not None.
    ct_fnmatch = param.String(default="*", doc="fnmatch for selecting ct files from ct_dir")
    ob_fnmatch = param.String(default="*", doc="fnmatch for selecting ob files from ob_dir")
    dc_fnmatch = param.String(default="*", doc="fnmatch for selecting dc files from dc_dir")
    # NOTE: 0 means use as many as possible
    max_workers = param.Integer(default=0, bounds=(0, None), doc="Maximum number of processes allowed during loading")

    def __call__(self, **params):
        """
        This makes the class behaves like a function.
        """
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = multiprocessing.cpu_count() - 2 if params.max_workers == 0 else params.max_workers
        logger.debug(f"max_worker={self.max_workers}")

        # multiple dispatch
        # NOTE:
        #    use set to simplify call signature checking
        sigs = set([k.split("_")[-1] for k in params.keys() if "fnmatch" not in k])
        if sigs == {"files", "dir"}:
            logger.error("Files and dir cannot be used at the same time")
            raise ValueError("Mix usage of allowed signature.")
        elif sigs == {"files"}:
            logger.debug("Load by file list")
            ct, ob, dc = _load_by_file_list(
                ct_files=params.get("ct_files"),
                ob_files=params.get("ob_files"),
                dc_files=params.get("dc_files", []),  # it is okay to skip dc
                ct_fnmatch=params.get("ct_fnmatch", "*"),  # incase None got leaked here
                ob_fnmatch=params.get("ob_fnmatch", "*"),
                dc_fnmatch=params.get("dc_fnmatch", "*"),
            )
            ct_files = params.get("ct_files")
        elif sigs == {"dir"}:
            logger.debug("Load by directory")
            ct_files, ob_files, dc_files = _get_filelist_by_dir(
                ct_dir=params.get("ct_dir"),
                ob_dir=params.get("ob_dir"),
                dc_dir=params.get("dc_dir", []),  # it is okay to skip dc
                ct_fnmatch=params.get("ct_fnmatch", "*"),  # incase None got leaked here
                ob_fnmatch=params.get("ob_fnmatch", "*"),
                dc_fnmatch=params.get("dc_fnmatch", "*"),
            )
            ct, ob, dc = _load_by_file_list(
                ct_files=ct_files,
                ob_files=ob_files,
                dc_files=dc_files,
                ct_fnmatch=params.get("ct_fnmatch", "*"),  # incase None got leaked here
                ob_fnmatch=params.get("ob_fnmatch", "*"),
                dc_fnmatch=params.get("dc_fnmatch", "*"),
            )
        else:
            logger.warning("Found unknown input arguments, ignoring.")

        # extracting omegas from
        # 1. filename
        # 2. metadata (only possible for Tiff)
        rot_angles = _extract_rotation_angles(ct_files)

        # return everything
        return ct, ob, dc, rot_angles


# use _func to avoid sphinx pulling it into docs
def _forgiving_reader(
    filename: str,
    reader: Optional[Callable],
) -> Optional[np.ndarray]:
    """
    Skip corrupted file, but inform the user about the issue.

    Parameters
    ----------
    filename:
        input filename
    reader:
        callable reader function that consumes the filename

    Returns
    -------
        image as numpy array
    """
    try:
        return reader(filename)
    except:
        logger.error(f"Cannot read {filename}, skipping.")
        return None


# use _func to avoid sphinx pulling it into docs
def _load_images(
    filelist: List[str],
    desc: str,
    max_workers: int,
) -> np.ndarray:
    """
    Load image data via dxchange.

    Parameters
    ----------
    filelist:
        List of images filenames/path for loading via dxchange.
    desc:
        Description for progress bar.
    max_workers:
        Maximum number of processes allowed during loading.

    Returns
    -------
        Image array stack.
    """
    # figure out the file type and select corresponding reader from dxchange
    file_ext = Path(filelist[0]).suffix.lower()
    if file_ext in (".tif", ".tiff"):
        reader = dxchange.read_tiff
    elif file_ext == ".fits":
        reader = dxchange.read_fits
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        raise ValueError("Unsupported file type.")
    # read the data into numpy array via map_process
    rst = process_map(
        partial(_forgiving_reader, reader=reader),
        filelist,
        max_workers=max_workers,
        desc=desc,
    )
    # return the results
    return np.array([me for me in rst if me is not None])


# use _func to avoid sphinx pulling it into docs
def _load_by_file_list(
    ct_files: List[str],
    ob_files: List[str],
    dc_files: Optional[List[str]] = [],
    ct_fnmatch: Optional[str] = "*",
    ob_fnmatch: Optional[str] = "*",
    dc_fnmatch: Optional[str] = "*",
    max_workers: int = 0,
) -> Tuple[np.ndarray]:
    """
    Use provided list of files to load images into memory.

    Parameters
    ----------
    ct_files:
        List of ct files.
    ob_files:
        List of ob files.
    dc_files:
        List of dc files.
    ct_fnmatch:
        fnmatch for selecting ct files from ct_dir.
    ob_fnmatch:
        fnmatch for selecting ob files from ob_dir.
    dc_fnmatch:
        fnmatch for selecting dc files from dc_dir.
    max_workers:
        Maximum number of processes allowed during loading, 0 means
        use as many as possible.

    Returns
    -------
        ct, ob, dc
    """
    # empty list is not allowed
    if ct_files == []:
        logger.error("ct_files is [].")
        raise ValueError("ct_files cannot be empty list.")
    if ob_files == []:
        logger.error("ob_files is [].")
        raise ValueError("ob_files cannot be empty list.")
    if dc_files == []:
        logger.warning("dc_files is [].")

    # explicit list is the most straight forward solution
    # -- radiograph
    ct = _load_images(
        filelist=[ctf for ctf in ct_files if fnmatchcase(ctf, ct_fnmatch)],
        desc="ct",
        max_workers=max_workers,
    )
    # -- open beam
    ob = _load_images(
        filelist=[obf for obf in ob_files if fnmatchcase(obf, ob_fnmatch)],
        desc="ob",
        max_workers=max_workers,
    )
    # -- dark current
    if dc_files == []:
        dc = None
    else:
        dc = _load_images(
            filelist=[dcf for dcf in dc_files if fnmatchcase(dcf, dc_fnmatch)],
            desc="dc",
            max_workers=max_workers,
        )
    #
    return ct, ob, dc


def _get_filelist_by_dir(
    ct_dir: str,
    ob_dir: str,
    dc_dir: Optional[str] = None,
    ct_fnmatch: Optional[str] = "*",
    ob_fnmatch: Optional[str] = "*",
    dc_fnmatch: Optional[str] = "*",
) -> Tuple[List[str], List[str], List[str]]:
    """
    Generate list of files from given directory and fnmatch for ct, ob, and dc.

    Parameters
    ----------
    ct_dir:
        Directory for ct files.
    ob_dir:
        Directory for ob files.
    dc_dir:
        Directory for dc files.
    ct_fnmatch:
        fnmatch for selecting ct files from ct_dir.
    ob_fnmatch:
        fnmatch for selecting ob files from ob_dir.
    dc_fnmatch:
        fnmatch for selecting dc files from dc_dir.

    Returns
    -------
        ct_files, ob_files, dc_files

    Notes
    -----
        If ob_fnmatch is set to None, the data loader will attempt to read the metadata
        embedded in the ct file to find obs with similar metadata.
    """
    # sanity check
    # -- radiograph
    if not Path(ct_dir).exists():
        logger.error(f"ct_dir {ct_dir} does not exist.")
        raise ValueError("ct_dir does not exist.")
    else:
        ct_dir = Path(ct_dir)
    # -- open beam
    if not Path(ob_dir).exists():
        logger.error(f"ob_dir {ob_dir} does not exist.")
        raise ValueError("ob_dir does not exist.")
    else:
        ob_dir = Path(ob_dir)
    # -- dark current
    if dc_dir is None:
        logger.warning("dc_dir is None.")
    elif not Path(dc_dir).exists():
        logger.warning(f"dc_dir {dc_dir} does not exist, treating as None.")
        dc_dir = None
    else:
        dc_dir = Path(dc_dir)

    # gather the ct_files
    ct_files = ct_dir.glob(ct_fnmatch)

    # gather the ob_files
    if ob_fnmatch is None:
        raise NotImplementedError("ob_fnmatch is None is not implemented yet.")
    else:
        ob_files = ob_dir.glob(ob_fnmatch)

    # gather the dc_files
    if dc_dir is None:
        dc_files = []
    else:
        if dc_fnmatch is None:
            raise NotImplementedError("dc_fnmatch is None is not implemented yet.")
        else:
            dc_files = dc_dir.glob(dc_fnmatch)

    return list(map(str, ct_files)), list(map(str, ob_files)), list(map(str, dc_files))


def _extract_rotation_angles(
    filelist: List[str],
    metadata_idx: int = 65039,
) -> np.ndarray:
    """
    Extract rotation angles in degrees from filename or metadata.

    Parameters
    ----------
    filelist:
        List of files to extract rotation angles from.
    metadata_idx:
        Index of metadata to extract rotation angle from, default is 65039.

    Returns
    -------
        rotation_angles
    """
    # sanity check
    if filelist == []:
        logger.error("filelist is [].")
        raise ValueError("filelist cannot be empty list.")

    # extract rotation angles from file names
    # Note
    # ----
    #   For the following file
    #       20191030_ironman_small_0070_300_440_0520.tiff
    #   the rotation angle is 300.44 degrees
    # If all given filenames follows the pattern, we will use the angles from
    # filenames. Otherwise, we will use the angles from metadata.
    regex = r"\d{8}_\S*_\d{4}_(?P<deg>\d{3})_(?P<dec>\d{3})_\d*\.tiff"
    matches = [re.match(regex, Path(f).name) for f in filelist]
    if all(matches):
        rotation_angles = np.array([float(".".join(m.groups())) for m in matches])
    else:
        # extract rotation angles from metadata
        file_ext = set([Path(f).suffix for f in filelist])
        if file_ext != {".tiff"}:
            logger.error("Only tiff files are supported.")
            raise ValueError("Rotation angle from metadata is only supported for Tiff.")
        # -- read metadata
        # img = tifffile.TiffFile("test_with_metadata_0.tiff")
        # img.pages[0].tags[65039].value
        # >> 'RotationActual:0.579840'
        rotation_angles = np.array(
            [float(tifffile.TiffFile(f).pages[0].tags[metadata_idx].value.split(":")[-1]) for f in filelist]
        )
    return rotation_angles


# -----------------------------------
# TODO
# def _filter_by_metadata():
#     """
#     TODO: waiting on TIFFMetaData class
#     """
#     raise NotImplementedError
