#!/usr/bin/env python
from pathlib import Path
import sys


# declare the conda environment for this to run in
CONDA_ENV = "imars3d-dev"


def _validate_inputs(inputfile: Path, outputdir: Path) -> int:
    input_checking = 0
    if not inputfile.is_file():
        print(f"{inputfile} is not a file")
        input_checking += 1
    if not outputdir.is_dir():
        print(f"{outputdir} is not a directory")
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
    print("INPUT:", inputfile)  # TODO remove
    print("OUTPUT:", outputdir)  # TODO remove

    # verify the inputs are sensible
    input_checking = _validate_inputs(inputfile, outputdir)
    if input_checking > 0:
        return input_checking

    # TODO everything else

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: reduce_CG1D.py <inputfile> <outputdir>")
        sys.exit(-1)

    sys.exit(main(sys.argv[1], sys.argv[2]))
