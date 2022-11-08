#!/usr/bin/env python
from pathlib import Path
import sys
import logging
from datetime import datetime
from imars3d.backend.io.config import save_config
from imars3d.backend import auto_reduction_ready
from imars3d.backend import load_template_config
from imars3d.backend import extract_info_from_path
from imars3d.backend.workflow.engine import WorkflowEngineAuto


# declare the conda environment for this to run in
CONDA_ENV = "imars3d-dev"

logger = logging.getLogger("reduce_CG1D")


def _validate_inputs(inputfile: Path, outputdir: Path) -> int:
    input_checking = 0
    if not inputfile.is_file():
        logger.error(f"'{inputfile}' is not a file")
        input_checking += 1
    if not outputdir.is_dir():
        logger.error(f"'{outputdir}' is not a directory")
        input_checking += 1

    return input_checking


def main(inputfile: str, outputdir: str) -> int:
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
    logging.info("INPUT:", inputfile)  # TODO remove
    logging.info("OUTPUT:", outputdir)  # TODO remove

    # verify the inputs are sensible
    input_checking = _validate_inputs(inputfile, outputdir)
    if input_checking > 0:
        return input_checking

    # step 0: check if data is ready for reduction
    if not auto_reduction_ready(inputfile):
        logger.warning("Data incomplete, waiting for next try.")
        return 1

    # step 1: load the template configuration file to memory
    config_dict = load_template_config()

    # step 2: extract info from inputfile
    update_dict = extract_info_from_path(inputfile)

    # step 3: update the dict and save dict to disk
    config_dict.update(update_dict)
    # save config file to working directory
    # NOTE:
    #  i.e. ironman_20221108_154015.json
    exp_name = config_dict["name"].replace(" ", "_")
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    config_fn = outputdir / f"{exp_name}_{time_str}.json"
    save_config(config_dict, config_fn)

    # step 4: call the auto reduction with updated dict
    workflow = WorkflowEngineAuto(config_dict)
    return workflow.run()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: reduce_CG1D.py <inputfile> <outputdir>")
        sys.exit(-1)

    sys.exit(main(sys.argv[1], sys.argv[2]))
