# package imports
from imars3d.backend.workflow.engine import WorkflowEngineAuto, WorkflowValidationError

# third party imports
import numpy as np
from param import Parameter, ParameterizedFunction
from param.parameterized import String as StringParam

# standard library imports
from copy import deepcopy
import json
import pytest


class load_data(ParameterizedFunction):
    r"""mock loading a set of radiographs into a numpy array"""

    ct_files = Parameter(default=None)
    ct_dir = StringParam(default=None)

    def __call__(self, **params):
        return [
            np.arange(len(params["ct_files"])),
        ]


class save_data(ParameterizedFunction):
    r"""mock saving a set or radiographs to some directory"""

    ct = Parameter(default=None)
    workingdir = Parameter()

    def __call__(self, **params):
        return []


class find_rot_center(ParameterizedFunction):
    ct = Parameter(default=None)

    def __call__(self, **params):
        return [0.0]


class reconstruction(ParameterizedFunction):
    r"""mock the reconstruction of the radiographs"""

    ct = Parameter(default=None)
    rot_center = Parameter(default=None)

    def __call__(self, **params):
        return [
            params["ct"],
        ]


class reconstruction_with_default(ParameterizedFunction):
    r"""mock the reconstruction of the radiographs"""

    ct = Parameter(default=None)
    rot_center = Parameter(default=0.0)

    def __call__(self, **params):
        return [
            params["ct"],
        ]


@pytest.fixture(scope="module")
def config():
    config_str = """{
    "facility": "HFIR",
    "instrument": "CG1D",
    "ipts": "IPTS-1234",
    "name": "name for reconstructed ct scans",
    "workingdir": "/path/to/working/dir",
    "outputdir": "/path/to/output/dir",
    "tasks": [
        {
            "name": "task1",
            "function": "_MODULE_PATH_.load_data",
            "inputs": {
                "ct_files": ["ct1", "ct2", "ct3"],
                "ct_dir": "_MODULE_PATH_"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task3",
            "function": "_MODULE_PATH_.reconstruction_with_default",
            "outputs": ["ct"]
        },
        {
            "name": "task4",
            "function": "_MODULE_PATH_.reconstruction",
            "inputs": {
                "rot_center": 0.0
            },
            "outputs": ["ct2"]
        },
        {
            "name": "task5",
            "function": "_MODULE_PATH_.find_rot_center",
            "outputs": ["rot_center"]
        },
        {
            "name": "task6",
            "function": "_MODULE_PATH_.reconstruction",
            "inputs": {
                "ct": "ct2"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task2",
            "function": "_MODULE_PATH_.save_data"
        }
    ]
}"""
    return json.loads(config_str.replace("_MODULE_PATH_", __name__))


class TestWorkflowEngineAuto:
    def test_dryrun(self, config):
        workflow = WorkflowEngineAuto(config)
        workflow.load_data_function = f"{__name__}.load_data"
        workflow.save_data_function = f"{__name__}.save_data"
        workflow._dryrun()

    def test_dryrun_missing_input(self, config):
        # Error: task for which implicit ct has not been computed yet
        task0 = {"name": "task0", "function": f"{__name__}.save_data"}
        config_bad = deepcopy(config)
        config_bad["tasks"][0]["outputs"][0] = "ob"
        config_bad["tasks"].insert(1, task0)
        workflow = WorkflowEngineAuto(config_bad)
        workflow.load_data_function = f"{__name__}.load_data"
        workflow.save_data_function = f"{__name__}.save_data"
        with pytest.raises(WorkflowValidationError, match="ct for task task0 are missing"):
            workflow._dryrun()

    def test_dryrun_missing_rot(self, config):
        # Error: task for which templated rot_center has not been computed yet
        config_bad = deepcopy(config)
        config_bad["tasks"][2].pop("inputs")
        workflow = WorkflowEngineAuto(config_bad)
        workflow.load_data_function = f"{__name__}.load_data"
        workflow.save_data_function = f"{__name__}.save_data"
        with pytest.raises(WorkflowValidationError, match="rot_center for task task4 are missing"):
            workflow._dryrun()

    def test_run(self, config):
        workflow = WorkflowEngineAuto(config)
        workflow.load_data_function = f"{__name__}.load_data"
        workflow.save_data_function = f"{__name__}.save_data"
        workflow.run()


if __name__ == "__main__":
    pytest.main([__file__])
