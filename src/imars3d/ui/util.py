#!/usr/bin/env python3
"""Helper functions for UI development.

The functions in this module are for UI development only.
In production, the functions should be replaced by the corresponding
RunEngine in the backend module.

To test

from imars3d.ui.utils import run_task

mtd = {}
demo_task = {
    "name": "load",
    "function": "imars3d.backend.dataio.data.load_data",
    "inputs": {
        "ct_dir": "/HFIR//CG1D/IPTS-25777/raw/ct_scans/iron_man",
        "ob_dir": "/HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/",
        "dc_dir": "/HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/",
        "ct_fnmatch": "*.tiff",
        "ob_fnmatch": "*.tiff",
        "dc_fnmatch": "*.tiff"
    },
    "outputs": ["ct", "ob", "dc", "rot_angles"]
}
run_task(mtd, task=demo_task)
"""


def run_task(mtd, task):
    """Temp solution to run individual tasks.

    A permanent solution will be provided via RunEngine instead of using
    eval.
    """
    # parse function handle
    module_str = task["function"].split(".")[0]
    func_str = ".".join(task["function"].split(".")[1:])
    # prepare inputs
    argstr = []
    for k, v in task["inputs"].items():
        if v in mtd:
            argstr.append(f"{k}={v}")
        else:
            argstr.append(f"{k}='{v}'")
    argstr = ",".join(argstr)
    # build call str
    evalstr = f"__import__('{module_str}').{func_str}({argstr})"
    # call
    rst = eval(evalstr, {}, mtd)
    # update
    for ok, ov in zip(task["outputs"], rst):
        mtd[ok] = ov
