# package imports
from imars3d.backend.workflow.engine import WorkflowEngine, WorkflowEngineError
from imars3d.backend.workflow.validate import SCHEMA

# third party imports
import numpy as np
from param import Parameter, ParameterizedFunction

# standard library imports
from copy import deepcopy
import json
import pytest


class load_data(ParameterizedFunction):
    r"""mock loading a set of radiographs into a numpy array"""
    ct_files = Parameter()
    ct_dir = Parameter()

    def __call__(self, **params):
        return [
            np.arange(len(params["ct_files"])),
        ]


class save(ParameterizedFunction):
    r"""mock saving a set or radiographs to some directory"""
    ct = Parameter()
    workingdir = Parameter()

    def __call__(self, **params):
        return None


class reconstruction(ParameterizedFunction):
    r"""mock the reconstruction of the radiographs"""
    ct = Parameter()
    rot_center = Parameter()

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
                "ct_files": ["ct1", "ct2", "ct3"]
            },
            "outputs": ["ct"]
        },
        {
            "name": "task2",
            "function": "_MODULE_PATH_.save"
        },
        {
            "name": "task3",
            "function": "_MODULE_PATH_.reconstruction",
            "inputs": {
                "rot_center": "0.0"
            },
            "outputs": ["ct"]
        }
    ]
}"""
    return json.loads(config_str.replace("_MODULE_PATH_", __name__))


class TestWorkflowEngine:
    engine = WorkflowEngine(workflow_schema=SCHEMA)  # engine is a workflow factory

    def test_dryrun(self, config):
        workflow = self.engine(config)
        workflow._dryrun()

        # Error: adding a templated output not in globals
        config_bad = deepcopy(config)
        config_bad["tasks"][1].update({"outputs": ["path"]})
        workflow = self.engine(config_bad)
        with pytest.raises(WorkflowEngineError, match="path of task task2 should be global"):
            workflow._dryrun()

        # Error: task for which implicit ct has not been computed yet
        task0 = {"name": "task0", "function": f"{__name__}.save", "outputs": ["ct"]}
        config_bad = deepcopy(config)
        config_bad["tasks"].insert(0, task0)
        workflow = self.engine(config_bad)
        with pytest.raises(WorkflowEngineError, match="ct for task task0 are missing"):
            workflow._dryrun()

        # Error: task for which templated rot_center has not been computed yet
        config_bad = deepcopy(config)
        config_bad["tasks"][2].pop("inputs")
        workflow = self.engine(config_bad)
        with pytest.raises(WorkflowEngineError, match="rot_center for task task3 are missing"):
            workflow._dryrun()

    def test_run(self, config):
        workflow = self.engine(config)
        workflow.run()


if __name__ == "__main__":
    pytest.main([__file__])
