# package imports
from imars3d.backend.workflow.engine import WorkflowEngine, WorkflowEngineError

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
    "instrument": "cg1d",
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
    def test_dryrun(self, config):
        engine = WorkflowEngine(config)
        engine._dryrun()

        # Error: adding a templated output not in globals
        config_bad = deepcopy(config)
        config_bad["tasks"][1].update({"outputs": ["path"]})
        engine = WorkflowEngine(config_bad)
        with pytest.raises(WorkflowEngineError, match="path of task task2 should be global"):
            engine._dryrun()

        # Error: task for which implicit ct has not been computed yet
        task0 = {"name": "task0", "function": f"{__name__}.save", "outputs": ["ct"]}
        config_bad = deepcopy(config)
        config_bad["tasks"].insert(0, task0)
        engine = WorkflowEngine(config_bad)
        with pytest.raises(WorkflowEngineError, match="ct for task task0 are missing"):
            engine._dryrun()

        # Error: task for which templated rot_center has not been computed yet
        config_bad = deepcopy(config)
        config_bad["tasks"][2].pop("inputs")
        engine = WorkflowEngine(config_bad)
        with pytest.raises(WorkflowEngineError, match="rot_center for task task3 are missing"):
            engine._dryrun()

    def test_run(self, config):
        engine = WorkflowEngine(config)
        engine.run()


if __name__ == "__main__":
    pytest.main([__file__])
