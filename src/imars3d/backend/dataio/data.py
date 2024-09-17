#!/usr/bin/env python3
"""Data handling for iMars3D."""

# package imports
from imars3d.backend.dataio.metadata import MetaData
from imars3d.backend.util.functions import clamp_max_workers, to_time_str

# third party imports
import numpy as np
import param
import tifffile
from tqdm.auto import tqdm
from tqdm.contrib.concurrent import process_map

# standard imports
from functools import partial
from fnmatch import fnmatchcase
import itertools
import logging
from pathlib import Path
import re
from typing import Callable, List, Optional, Tuple, Union

# ignore warnings generated by importing dxchange
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import dxchange

# Custom types
FlexPath = Union[str, Path]

# setup module level logger
logger = logging.getLogger(__name__)
# METADATA_DICT = {
#     65026: "ManufacturerStr:Andor",  # [ct, ob, dc]
#     65027: "ExposureTime:70.000000",  # [ct, ob, dc]
#     65068: "MotSlitHR.RBV:10.000000",  # APERTURE_HR, [ct, ob]
#     65070: "MotSlitHL.RBV:20.000000",  # APERTURE_HL, [ct, ob]
#     65066: "MotSlitVT.RBV:10.000000",  # APERTURE_VT, [ct, ob]
#     65068: "MotSlitHR.RBV:10.000000",  # APERTURE_VB, [ct, ob]
# }


class Foldernames(param.Foldername):
    r"""
    Parameter that can be set to a string specifying the path of a folder, or a list of such strings.

    The string(s) should be specified in UNIX style, but they will be
    returned in the format of the user's operating system.

    The specified path(s) can be absolute, or relative to either:

    * any of the paths specified in the search_paths attribute (if search_paths is not None);

    or

    * any of the paths searched by resolve_dir_path() (if search_paths is None).
    """

    def _validate(self, val):

        if isinstance(val, (list, tuple)):
            for v in val:
                super()._validate(v)
        else:
            super()._validate(val)

    def _resolve(self, paths):

        if isinstance(paths, (list, tuple)):
            return [self._resolve(path) for path in paths]
        else:
            return super()._resolve(paths)


class load_data(param.ParameterizedFunction):
    """
    Load data with given input.

    Parameters
    ----------
    ct_files: List[str]
        explicit list of radiographs (full path)
    ob_files: List[str]
        explicit list of open beams (full path)
    dc_files: Optional[List[str]]
        explicit list of dark current (full path)
    ct_dir: str, Path
        directory contains radiographs
    ob_dir: Union[str, Path, List[str, Path]]
        directory, or list of directories, containing open beams
    dc_dir: Optional[Union[str, Path, List[str, Path]]]
        directory , or list of directories, containing dark current
    ct_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting radiographs
    ob_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting open beams
    dc_fnmatch: Optional[str]
        Unix shells-style wild card (``*.tiff``) for selecting dark current
    max_workers: Optional[int]
        maximum number of processes allowed during loading, default to use a single core.
    tqdm_class: panel.widgets.Tqdm
        Class to be used for rendering tqdm progress

    Returns
    -------
        radiograph stacks, obs, dcs and rotation angles as numpy.ndarray

    Notes
    -----
        There are three main signatures to load the data:
        1. load_data(ct_files=ctfs, ob_files=obfs, dc_files=dcfs)
        2. load_data(ct_dir=ctdir, ob_dir=obdir, dc_dir=dcdir)
        3. load_data(ct_dir=ctdir, ob_files=obfs, dc_files=dcfs)

        In all signatures dc_files and dc_dir are optional

        The fnmatch selectors are applicable in all signature, which help to down-select
        files if needed. Default is set to "*", which selects everything.
        Also, if ob_fnmatch and dc_fnmatch are set to "None" in the second signature call, the
        data loader will attempt to read the metadata embedded in the first ct file to find obs
        and dcs with similar metadata.

        Currently, we are using a forgiving reader to load the image where a corrupted file
        will not block reading other data.

        The rotation angles are extracted from the filenames if possible, otherwise from the
        metadata embedded in the tiff files. If both failed, the angle will be set to None.
    """

    #
    ct_files = param.List(doc="list of all ct files to load")
    ob_files = param.List(doc="list of all ob files to load")
    dc_files = param.List(doc="list of all dc files to load")
    #
    ct_dir = param.Foldername(doc="radiograph directory")
    ob_dir = Foldernames(doc="open beam directory")
    dc_dir = Foldernames(doc="dark current directory")
    # NOTE: we need to provide a default value here as param.String default to "", which will
    #       not trigger dict.get(key, value) to get the value as "" is not None.
    ct_fnmatch = param.String(default="*", doc="fnmatch for selecting ct files from ct_dir")
    ob_fnmatch = param.String(default="*", doc="fnmatch for selecting ob files from ob_dir")
    dc_fnmatch = param.String(default="*", doc="fnmatch for selecting dc files from dc_dir")
    # NOTE: 0 means use as many as possible
    max_workers = param.Integer(
        default=1,  # default to single process
        bounds=(0, None),
        doc="Maximum number of processes allowed during loading",
    )
    tqdm_class = param.ClassSelector(class_=object, doc="Progress bar to render with")

    def __call__(self, **params):
        """Parse inputs and perform multiple dispatch."""
        # type*bounds check via Parameter
        _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)
        # type validation is done, now replacing max_worker with an actual integer
        self.max_workers = clamp_max_workers(params.max_workers)
        logger.debug(f"max_worker={self.max_workers}")

        # multiple dispatch
        # NOTE:
        #    use set to simplify call signature checking
        sigs = set([k.split("_")[-1] for k in params.keys() if "fnmatch" not in k])
        ref = {"files", "dir"}

        if ("ct_dir" in params.keys()) and ("ob_files" in params.keys()):
            logger.debug("Load ct by directory, ob and dc (if any) by files")
            ct_dir = params.get("ct_dir")
            if not Path(ct_dir).exists():
                logger.error(f"ct_dir {ct_dir} does not exist.")
                raise ValueError("ct_dir does not exist.")
            else:
                ct_dir = Path(ct_dir)

            # gather the ct_files
            ct_fnmatch = params.get("ct_fnmatch", "*")
            ct_files = ct_dir.glob(ct_fnmatch)
            ct_files = list(map(str, ct_files))
            ct_files.sort()

            ob_files = (params.get("ob_files"),)
            dc_files = (params.get("dc_files", []),)  # it is okay to skip dc

            ob_files = ob_files[0]
            dc_files = dc_files[0]

            ct, ob, dc = _load_by_file_list(
                ct_files=ct_files,
                ob_files=ob_files,
                dc_files=dc_files,  # it is okay to skip dc
                ct_fnmatch=params.get("ct_fnmatch", "*"),  # incase None got leaked here
                ob_fnmatch=params.get("ob_fnmatch", "*"),
                dc_fnmatch=params.get("dc_fnmatch", "*"),
                max_workers=self.max_workers,
                tqdm_class=params.tqdm_class,
            )

        elif ("ct_files" in params.keys()) and ("ob_dir" in params.keys()):
            logger.error("ct_files and ob_dir mixed not allowed!")
            raise ValueError("Mix signatures (ct_files, ob_dir) not allowed!")

        elif sigs.intersection(ref) == {"files"}:
            logger.debug("Load by file list")
            ct, ob, dc = _load_by_file_list(
                ct_files=params.get("ct_files"),
                ob_files=params.get("ob_files"),
                dc_files=params.get("dc_files", []),  # it is okay to skip dc
                ct_fnmatch=params.get("ct_fnmatch", "*"),  # incase None got leaked here
                ob_fnmatch=params.get("ob_fnmatch", "*"),
                dc_fnmatch=params.get("dc_fnmatch", "*"),
                max_workers=self.max_workers,
                tqdm_class=params.tqdm_class,
            )
            ct_files = params.get("ct_files")
        elif sigs.intersection(ref) == {"dir"}:
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
                max_workers=self.max_workers,
                tqdm_class=params.tqdm_class,
            )
        else:
            logger.warning("No valid signature found, need to specify either files or dir")
            raise ValueError("No valid signature found, need to specify either files or dir")

        # extracting rotational angles from
        # 1. filename
        # 2. metadata (only possible for Tiff)
        rot_angles = _extract_rotation_angles(ct_files)

        # return everything
        return ct, ob, dc, rot_angles


# use _func to avoid sphinx pulling it into docs
def _forgiving_reader(
    filename: str,
    reader: Callable,
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
    except Exception as e:
        logger.error(f"While reading {filename}, the following error occurred: {e}")
        return None


# use _func to avoid sphinx pulling it into docs
def _load_images(filelist: List[str], desc: str, max_workers: int, tqdm_class) -> np.ndarray:
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
    tqdm_class: panel.widgets.Tqdm
        Class to be used for rendering tqdm progress

    Returns
    -------
        Image array stack.
    """
    # figure out the file type and select corresponding reader from dxchange
    file_ext = Path(filelist[0]).suffix.lower()
    if file_ext in (".tif", ".tiff"):
        # use tifffile directly for a faster loading
        # NOTE: Test conducted on 09-05-2024 on bl10-analysis1 shows that using
        #       memmap is faster, which contradicts the observation from the instrument
        #       team.
        #                       | Method | Time (s) |
        #                       |--------|----------|
        #                       | `imread(out="memmap")` | 2.62 s ± 24.6 ms |
        #                       | `imread()` | 3.59 s ± 13.6 ms |
        #       The `memmap` option is removed until we have a better understanding of the
        #       discrepancy.
        # reader = partial(tifffile.imread, out="memmap")
        reader = tifffile.imread
    elif file_ext == ".fits":
        reader = dxchange.read_fits
    else:
        logger.error(f"Unsupported file type: {file_ext}")
        raise ValueError("Unsupported file type.")

    # NOTE: For regular dataset, single thread reading is actually faster
    #       as the overhead of multiprocessing will overshadow the benefits.
    if max_workers == 1:
        progress_bar = tqdm if tqdm_class is None else tqdm_class
        # single thread reading
        rst = [_forgiving_reader(f, reader) for f in progress_bar(filelist, desc=desc)]
    else:
        # multi-thread reading
        # NOTE: the benefits of multi-threading is only visible when
        #       - the file list is really long
        #       - there are a lot of cores available
        kwargs = {
            "max_workers": max_workers,
            "desc": desc,
        }
        rst = process_map(partial(_forgiving_reader, reader=reader), filelist, **kwargs)

    # return the results
    # NOTE: there is no need to convert to float at this point, and it will save
    #       a lot of memory and time if the conversion is done after cropping.
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
    tqdm_class=None,
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
    tqdm_class: panel.widgets.Tqdm
        Class to be used for rendering tqdm progress

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

    max_workers = clamp_max_workers(max_workers)
    # explicit list is the most straight forward solution
    # -- radiograph
    ct = _load_images(
        filelist=[ctf for ctf in ct_files if fnmatchcase(ctf, ct_fnmatch)],
        desc="ct",
        max_workers=max_workers,
        tqdm_class=tqdm_class,
    )
    # -- open beam
    ob = _load_images(
        filelist=[obf for obf in ob_files if fnmatchcase(obf, ob_fnmatch)],
        desc="ob",
        max_workers=max_workers,
        tqdm_class=tqdm_class,
    )
    # -- dark current
    if dc_files == []:
        dc = None
    else:
        dc = _load_images(
            filelist=[dcf for dcf in dc_files if fnmatchcase(dcf, dc_fnmatch)],
            desc="dc",
            max_workers=max_workers,
            tqdm_class=tqdm_class,
        )
    #
    return ct, ob, dc


def _get_filelist_by_dir(
    ct_dir: FlexPath,  # either a string or a pathlib.Path
    ob_dir: Union[FlexPath, List[FlexPath]],
    dc_dir: Optional[Union[FlexPath, List[FlexPath]]] = None,
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
        Directory, or list of directories, for ob files.
    dc_dir:
        Directory, or list of directories, for dc files.
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
    ##########
    # -- Process input argument ct_dir for radiographs
    if not Path(ct_dir).exists():
        logger.error(f"ct_dir {ct_dir} does not exist.")
        raise ValueError("ct_dir does not exist.")
    else:
        ct_dir = Path(ct_dir)
    ##########
    # -- Process input argument ob_dir for open beam directories
    if isinstance(ob_dir, (str, Path)):  # single directory
        open_beam_dirs = [Path(ob_dir)]  # cast the single directory to a list of input directories
    elif isinstance(ob_dir, (list, tuple)):  # multiple input directories, assumed items are of FlexPath type
        open_beam_dirs = [Path(data_dir) for data_dir in ob_dir]
    else:
        raise ValueError("ob_dir must be either a string or a list of strings")
    # validate for existence
    for data_dir in open_beam_dirs:
        if not data_dir.exists():
            logger.error(f"open beam directory {str(data_dir)} does not exist.")
            raise ValueError(f"open beam directory {str(data_dir)} does not exist.")
    ##########
    # -- Process input argument dc_dir for dark current directories
    if dc_dir is None:
        logger.warning("dc_dir is None, ignoring.")
        dark_field_dirs = []
    else:
        if isinstance(dc_dir, (str, Path)):  # single directory
            dark_field_dirs = [Path(dc_dir)]  # cast the single directory to a list of input directories
        elif isinstance(dc_dir, (list, tuple)):  # multiple directories, assumed items are of FlexPath type
            dark_field_dirs = [Path(data_dir) for data_dir in dc_dir]
        else:
            raise ValueError("dc_dir must be either a string or a list of strings")
    # check for existence
    for i, data_dir in enumerate(dark_field_dirs):
        if not data_dir.exists():
            logger.warning(f"dark field directory {str(data_dir)} does not exist, ignoring.")
            dark_field_dirs[i] = None
    dark_field_dirs = [data_dir for data_dir in dark_field_dirs if data_dir is not None]  # extricate None entries

    # gather the ct_files
    ct_files = ct_dir.glob(ct_fnmatch)
    # try to use the first ct file as a reference
    # NOTE: do not use the generator above to avoid off by one error due to
    #       consuming the generator
    try:
        ct_ref = next(ct_dir.glob(ct_fnmatch))
    except StopIteration:
        logger.warning("ct_files is [].")
        ct_ref = None
    metadata_ref = None if ct_ref is None else MetaData(filename=str(ct_ref), datatype="ct")
    ext_ref = None if ct_ref is None else ct_ref.suffix

    # gather the ob_files
    if ob_fnmatch is None:
        if ct_ref is None:
            logger.warning("ob_files is [].")
            ob_files = []
        else:
            ob_files = list()
            for open_beam_dir in open_beam_dirs:
                obfs = open_beam_dir.glob(f"*{ext_ref}")
                # remove files that do not match the metadata of ct_ref
                ob_files += [f for f in obfs if metadata_ref.match(other_filename=str(f), other_datatype="ob")]
    else:
        ob_files = list(itertools.chain(*[list(obd.glob(ob_fnmatch)) for obd in open_beam_dirs]))

    # gather the dc_files
    if dc_dir is None:
        dc_files = []
    else:
        if dc_fnmatch is None:
            if ct_ref is None:
                logger.warning("dc_files is [].")
                dc_files = []
            else:
                dc_files = list()
                for dark_field_dir in dark_field_dirs:
                    dcfs = dark_field_dir.glob(f"*{ext_ref}")
                    # remove files that do not match the metadata of ct_ref
                    dc_files += [f for f in dcfs if metadata_ref.match(other_filename=str(f), other_datatype="dc")]
        else:
            dc_files = list(itertools.chain(*[list(dcf.glob(dc_fnmatch)) for dcf in dark_field_dirs]))

    # since generator returns an unordered list, we need to force it to be sorted
    # so that angles can be properly retrieved if needed
    ct_files = list(map(str, ct_files))
    ct_files.sort()

    return ct_files, list(map(str, ob_files)), list(map(str, dc_files))


def _extract_rotation_angles(
    filelist: List[str],
    metadata_idx: int = 65039,
) -> Optional[np.ndarray]:
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
            Array of rotation angles if successfully extracted, None otherwise.
    """
    # sanity check
    if not filelist:
        logger.error("filelist is [].")
        raise ValueError("filelist cannot be empty list.")

    # process one file at a time
    rotation_angles = []
    for filename in filelist:
        file_ext = Path(filename).suffix.lower()
        angle = None
        if file_ext == ".tiff":
            # first, let's try to extract the angle from the filename
            angle = extract_rotation_angle_from_filename(filename)
            if angle is None:
                # if failed, try to extract from metadata
                angle = extract_rotation_angle_from_tiff_metadata(filename, metadata_idx)
            if angle is None:
                # if failed, log a warning and move on
                logger.warning(f"Failed to extract rotation angle from {filename}.")
        elif file_ext in (".tif", ".fits"):
            # for tif and fits, we can only extract from filename as the metadata is not reliable
            angle = extract_rotation_angle_from_filename(filename)
            if angle is None:
                # if failed, log a warning and move on
                logger.warning(f"Failed to extract rotation angle from {filename}.")
        else:
            # if the file type is not supported, raise value error
            logger.error(f"Unsupported file type: {file_ext}")
            raise ValueError("Unsupported file type.")

        rotation_angles.append(angle)

    # this means we have a list of None
    if all(angle is None for angle in rotation_angles):
        logger.warning("Failed to extract any rotation angles.")
        return None

    # warn users if some angles are missing
    if any(angle is None for angle in rotation_angles):
        logger.warning("Some rotation angles are missing. You will see nan in the rotation angles array.")

    return np.array(rotation_angles, dtype=float)


def extract_rotation_angle_from_filename(filename: str) -> Optional[float]:
    """
    Extract rotation angle in degrees from filename.

    Parameters
    ----------
    filename:
        Filename to extract rotation angle from.

    Returns
    -------
        rotation_angle
            Rotation angle in degrees if successfully extracted, None otherwise.
    """
    # extract rotation angle from file names
    # Note
    # ----
    #   For the following file
    #       20191030_ironman_small_0070_300_440_0520.tif(f)
    #       20191030_ironman_small_0070_300_440_0520.fits
    #   the rotation angle is 300.44 degrees
    regex = r"\d{8}_\S*_\d{4}_(?P<deg>\d{3})_(?P<dec>\d{3})_\d*\.(?:tiff?|fits)"
    match = re.match(regex, Path(filename).name)
    if match:
        rotation_angle = float(".".join(match.groups()))
    else:
        rotation_angle = None
    return rotation_angle


def extract_rotation_angle_from_tiff_metadata(filename: str, metadata_idx: int = 65039) -> Optional[float]:
    """
    Extract rotation angle in degrees from metadata of a tiff file.

    Parameters
    ----------
    filename:
        Filename to extract rotation angle from.
    metadata_idx:
        Index of metadata to extract rotation angle from, default is 65039.

    Returns
    -------
        rotation_angle
            Rotation angle in degrees if successfully extracted, None otherwise.
    """
    try:
        # -- read metadata
        # img = tifffile.TiffFile("test_with_metadata_0.tiff")
        # img.pages[0].tags[65039].value
        # >> 'RotationActual:0.579840'
        return float(tifffile.TiffFile(filename).pages[0].tags[metadata_idx].value.split(":")[-1])
    except Exception:
        return None


def _save_data(filename: Path, data: np.ndarray, rot_angles: np.ndarray = None) -> None:
    if data is None:
        raise ValueError("Failed to supply data")
    logger.info(f'saving tiffs to "{filename.parent}"')

    # make sure the directory exists
    if not filename.parent.exists():
        filename.parent.mkdir(parents=True)
    # save the stack of tiffs
    dxchange.write_tiff_stack(data, fname=str(filename))

    # save the angles as a numpy object
    if rot_angles is not None:
        np.save(file=filename.parent / "rot_angles.npy", arr=rot_angles)


class save_data(param.ParameterizedFunction):
    """
    Save data with given input.

    The filenames will be
    ``<outputbase>/<name>_YYYYMMDDhhmm/<name>_####.tiff``
    where a canonical ``outputbase`` is ``/HFIR/CG1D/IPTS-23788/shared/processed_data/``.

    Parameters
    ----------
    data: Array
        array of data to save
    outputbase: Path
        where to save the output on disk.
        ``param.Foldername`` will warn if the directory does not already exist.
    name: str
        Used to name file of output, defaults to ``save_data``
    rot_angles: Array
        Optional for writing out the array of rotational (omega) angles

    Returns
    -------
        The directory the files were actually saved in
    """

    data = param.Array(doc="Data to save", precedence=1)
    outputbase = param.Foldername(default="/tmp/", doc="radiograph directory")
    name = param.String(default="save_data", doc="name for the radiograph")
    rot_angles = param.Array(doc="Collection of omega angles")

    def __call__(self, **params):
        """Parse inputs and perform multiple dispatch."""
        # type bounds check via Parameter
        with param.logging_level("CRITICAL"):
            # do not complain about directories that don't exist
            _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)

        if params.data is None:
            raise ValueError("Did not supply data")

        save_dir = Path(params.outputbase) / f"{params.name}_{to_time_str()}"

        # save the data as tiffs
        _save_data(filename=save_dir / params.name, data=params.data, rot_angles=params.rot_angles)

        return save_dir


class save_checkpoint(param.ParameterizedFunction):
    """
    Save current state to checkpoint in a datetime stamped directory name.

    The filenames will be
    ``<outputbase>/<name>_chkpt_YYYYMMDDhhmm/<name>_####.tiff``
    where a canonical ``outputbase`` is ``/HFIR/CG1D/IPTS-23788/shared/processed_data/``.

    Parameters
    ----------
    data: Array
        array of data to save
    outputbase: Path
        The parent directory of where to save the output on disk.
        ``param.Foldername`` will warn if the directory does not already exist.
    name: str
        Used to name file of output, defaults to output_{datetime}
    rot_angles: Array
        Optional for writing out the array of rotational (omega) angles

    Returns
    -------
        The directory the files were actually saved in
    """

    data = param.Array(doc="Data to save", precedence=1)
    outputbase = param.Foldername(default="/tmp/", doc="directory checkpoint should exist in")

    name = param.String(default="*", doc="name for the checkpoint")
    rot_angles = param.Array(doc="Collection of rotational (omega) angles")

    def __call__(self, **params):
        """Parse inputs and perform multiple dispatch."""
        # type bounds check via Parameter
        with param.logging_level("CRITICAL"):
            # do not complain about directories that don't exist
            _ = self.instance(**params)
        # sanitize arguments
        params = param.ParamOverrides(self, params)

        save_dir = params.outputbase / f"{params.name}_chkpt_{to_time_str()}"

        # save the data as tiffs
        _save_data(filename=save_dir / params.name, data=params.data, rot_angles=params.rot_angles)

        return save_dir
