#!/usr/bin/env python

# package imports
from imars3d.backend.dataio.config import save_config
from imars3d.backend import auto_reduction_ready
from imars3d.backend import load_template_config
from imars3d.backend import extract_info_from_path
from imars3d.backend import substitute_template
from imars3d.backend.autoredux import logger as logger_autoredux
from imars3d.backend.workflow.engine import WorkflowEngineAuto, WorkflowEngineError, WorkflowEngineExitCodes
from imars3d.backend.util.functions import to_time_str

# standard imports
import logging
from pathlib import Path
import shutil
from typing import Union
import sys

# declare the conda environment for this to run in
CONDA_ENV = "imars3d-dev"
ERROR_GENERAL = -1  # for things that aren't workflow
SCAN_INCOMPLETE = 10  # TODO need to discus this
WORKFLOW_SUCCESS: int = WorkflowEngineExitCodes.SUCCESS.value

logger = logger_autoredux.getChild("reduce_CG1D")


def _validate_inputs(inputfile: Path, outputdir: Path) -> int:
    """This returns the number of inputs that are broken.
    The result is useful for a return code"""
    input_checking = 0
    if not inputfile.is_file():
        logger.error(f"'{inputfile}' is not a file")
        input_checking += 1
    if not outputdir.is_dir():
        logger.error(f"'{outputdir}' is not a directory")
        input_checking += 1

    return input_checking


def _find_template_config() -> Path:
    r"""The template configuration file:
    1. is located in the same directory as this script.
    2. its name is 'reduce_CG1D_config_template.json'
    """
    template_name = "reduce_CG1D_config_template.json"
    autored_dir = Path(__file__).parent
    path_to_file = autored_dir / template_name
    if not path_to_file.exists():
        raise FileNotFoundError(f"Template {template_name} not found in directory {autored_dir}")
    return path_to_file


def main(inputfile: Union[str, Path], outputdir: Union[str, Path]) -> int:
    """
    Parameters:
    -----------
    inputfile:
        The full path to a ``.tiff`` file
    outputdir:
        The full path of where to write reconstruction to

    Returns
    -------
    Return code for use by ``sys.exit``.
    Zero means everything is fine any other value means failure
    """

    # convert the parameters to make the rest easier
    inputfile = Path(inputfile)
    outputdir = Path(outputdir)

    time_str = to_time_str()  # date stamp for log and configuration files

    # create log file to capture the root logger, in order to also capture messages from the backend
    log_file_path = outputdir / f"reduce_CG1D_{time_str}.log"
    log_file_handler = logging.FileHandler(log_file_path)
    log_file_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_file_handler)

    # verify the inputs are sensible
    input_checking = _validate_inputs(inputfile, outputdir)
    if input_checking > 0:
        return input_checking

    # check if data is ready for reduction
    if not auto_reduction_ready(inputfile):
        logger.warning("Data incomplete, waiting for next try.")
        return SCAN_INCOMPLETE

    # load the template configuration file to memory
    try:
        config_path = _find_template_config()
        config_dict = load_template_config(config_path)
    except FileNotFoundError:
        logger.exception("Unable to load the template configuration")
        return ERROR_GENERAL

    # extract info from inputfile
    update_dict = extract_info_from_path(str(inputfile))
    assert update_dict["instrument"] == "CG1D", "Instrument is not CG1D"
    update_dict["outputdir"] = str(outputdir)
    update_dict["workingdir"] = str(outputdir)

    # update the dict and save dict to disk
    try:
        config_dict = substitute_template(config_dict, update_dict)
    except Exception:
        logger.exception("Unable to update the template configuration")
        return ERROR_GENERAL

    # call the auto reduction with updated dict
    try:
        workflow = WorkflowEngineAuto(config_dict)
        workflow.run()
        exit_code = WORKFLOW_SUCCESS
    except WorkflowEngineError as e:
        logger.exception("Failed to create and run workflow")
        exit_code = e.exit_code

    # save configuration and log files to appropriate directory
    config_file_name = config_dict["name"].replace(" ", "_")
    radiographs_dir = workflow.registry.get("save_dir")
    if exit_code == WORKFLOW_SUCCESS and radiographs_dir:
        config_file_path = radiographs_dir / f"{config_file_name}_{time_str}.json"
        save_config(config_dict, config_file_path)
        logging.shutdown()  # flushing and closing all handlers
        shutil.move(log_file_path, radiographs_dir)  # move the log file to the radiographs directory
    else:
        config_file_path = outputdir / f"{config_file_name}_{time_str}.json"
        save_config(config_dict, config_file_path)

    return exit_code


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: reduce_CG1D.py <inputfile> <outputdir>")
        sys.exit(-1)

    sys.exit(main(sys.argv[1], sys.argv[2]))
