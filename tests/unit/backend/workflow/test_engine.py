# package imports
from imars3d.backend.workflow.engine import WorkflowEngine, WorkflowEngineError

# third party imports
import numpy as np
from param import Parameter, ParameterizedFunction

# standard library imports
from copy import deepcopy
import json
from pathlib import Path
import pytest


class load_data(ParameterizedFunction):
    r"""mimic loading a set of radiographs into a numpy array"""
    ct_files = Parameter()
    ct_dir = Parameter()

    def __call__(self):
        return np.arange(len(self.ct_files))


class save(ParameterizedFunction):
    r"""mimic saving a set or radiographs to some directory"""
    ct = Parameter()
    outputdir = Parameter()

    def __call__(self):
        return self.ct, self.outputdir / "out.dat"


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
                "ct_files": []
            },
            "outputs": ["ct"]
        },
        {
            "name": "task2",
            "function": "_MODULE_PATH_.save",
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
        config_bad["tasks"][1]["outputs"].append("path")
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

        # Error: task for which templated db has not been computed yet
        config_bad = deepcopy(config)
        config_bad["tasks"][1]["inputs"] = {"open_beam": "ob"}
        engine = WorkflowEngine(config_bad)
        with pytest.raises(WorkflowEngineError, match="ob for task task2 are missing"):
            engine._dryrun()

    r"""
    def test_run(self, config):
        engine = WorkflowEngine(config)
        engine.run()
    """


if __name__ == "__main__":
    pytest.main([__file__])
