# backend module integration tests

# package imports
from imars3d.backend.workflow.engine import WorkflowEngineAuto
from imars3d.backend.workflow.engine import WorkflowEngineError
from imars3d.backend.workflow.validate import JSONValidationError

# third party imports
import pytest

# standard library imports
from copy import deepcopy
import json
import numpy as np
from pathlib import Path
import dxchange
import shutil


@pytest.fixture(scope="module")
def THIS_DATA_DIR(DATA_DIR):
    return DATA_DIR.parent / "integration" / "backend"


ROI_X = (400, 600)
ROI_Y = (400, 600)


@pytest.fixture(scope="module")
def CONFIG_FILE(JSON_DIR):
    return JSON_DIR / "good_non_interactive_full.json"


@pytest.fixture(scope="module")
def config(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as handle:
        result = json.load(handle)
    return result


def crop_roi(slice_input):
    return slice_input[ROI_X[0] : ROI_X[1]][ROI_Y[0] : ROI_Y[1]]


class TestWorkflowEngineAuto:
    outputdir = "/tmp/imars3d/"

    @pytest.fixture(autouse=True)
    def buildup_teardown(self, tmpdir):
        """Fixture to execute asserts before and after a test is run"""
        # Setup: fill with any logic you want
        shutil.rmtree(path=self.outputdir, ignore_errors=True)
        yield  # this is where the testing happens
        shutil.rmtree(path=self.outputdir, ignore_errors=True)

    @pytest.mark.datarepo
    def test_config(self, config):
        workflow = WorkflowEngineAuto(config)
        assert workflow.config == config

    @pytest.mark.datarepo
    def test_run(self, config, THIS_DATA_DIR):
        workflow = WorkflowEngineAuto(config)
        expected_slice_300 = np.load(str(THIS_DATA_DIR / "expected_slice_300.npy"))
        workflow.run()
        # extract slice and crop to region of interest
        result = dxchange.read_tiff(self.outputdir + "test*")
        slice_300 = crop_roi(result[300])
        np.allclose(slice_300, expected_slice_300)

    def test_no_config(self):
        with pytest.raises(TypeError):
            workflow = WorkflowEngineAuto()
            workflow.run()

        with pytest.raises(json.decoder.JSONDecodeError):
            workflow = WorkflowEngineAuto("")
            workflow.run()

    def test_invalid_config(self, JSON_DIR):
        # tests an invalid configuration (no facility present)
        INVALID_CONFIG_FILE = JSON_DIR / "invalid_test.json"
        with pytest.raises(JSONValidationError):
            with open(INVALID_CONFIG_FILE, "r") as file:
                workflow = WorkflowEngineAuto(json.load(file))
                workflow.run()

    def test_invalid_workflow(self, JSON_DIR):
        INVALID_WORKFLOW_FILE = JSON_DIR / "invalid_workflow.json"
        with pytest.raises(WorkflowEngineError):
            with open(INVALID_WORKFLOW_FILE, "r") as file:
                workflow = WorkflowEngineAuto(json.load(file))
                workflow.run()

    def test_bad_filter_name_config(self, JSON_DIR):
        BAD_FILTER_JSON = JSON_DIR / "bad_filter.json"
        with pytest.raises(JSONValidationError):
            with open(BAD_FILTER_JSON, "r") as config:
                workflow = WorkflowEngineAuto(json.load(config))
                workflow.run()

    def test_incomplete_workflow(self, JSON_DIR):
        INCOMPLETE_WORKFLOW_JSON = JSON_DIR / "incomplete_workflow.json"
        with pytest.raises(WorkflowEngineError):
            with open(INCOMPLETE_WORKFLOW_JSON, "r") as config:
                workflow = WorkflowEngineAuto(json.load(config))
                workflow.run()

    def test_typo_input_parameter(self, config):
        r"""User writes 'array' instead of 'arrays' as one of the input parameters"""
        bad = deepcopy(config)
        bad["tasks"][1]["inputs"].pop("arrays")
        bad["tasks"][1]["inputs"]["array"] = "ct"
        workflow = WorkflowEngineAuto(bad)
        with pytest.raises(WorkflowEngineError) as e:
            workflow.run()
            assert 'Parameter(s) "array" are not input parameters' in str(e.value)

    def test_typo_output_parameter(self, config):
        r"""User write 'rot_angle' instead of 'rot_angles' as one of the outputs of task1.
        As a result, task7 will fail because it requires output 'rot_angles'"""
        bad = deepcopy(config)
        assert "load_data" in bad["tasks"][0]["function"]
        bad["tasks"][0]["outputs"][-1] = "rot_angle"
        workflow = WorkflowEngineAuto(bad)
        with pytest.raises(WorkflowEngineError) as e:
            workflow.run()
            assert 'Input(s) "rot_angles" for task task7 are missing' == str(e.value)

    def test_forgot_task(self, config):
        r"""User forgets to find the rotation center"""
        bad = deepcopy(config)
        # delete the task that finds the rotation center
        assert "find_rotation_center" in bad["tasks"][8]["function"]
        del bad["tasks"][8]
        workflow = WorkflowEngineAuto(bad)
        with pytest.raises(WorkflowEngineError) as e:
            workflow.run()
            assert 'Input(s) "rot_center" for task task8 are missing' == str(e.value)

    def test_forgot_input_parameter(self, config):
        r"""User forgets to pass input parameter 'darks' in the normalization task"""
        bad = deepcopy(config)
        assert "normalization" in bad["tasks"][5]["function"]
        del bad["tasks"][5]["inputs"]["darks"]
        workflow = WorkflowEngineAuto(bad)
        with pytest.raises(WorkflowEngineError) as e:
            workflow.run()
            assert 'Input(s) "darks" for task task4 are missing' == str(e.value)


if __name__ == "__main__":
    pytest.main([__file__])
