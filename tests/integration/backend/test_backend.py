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
import os, os.path
import shutil

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "integration" / "backend"
ROI_X = (400, 600)
ROI_Y = (400, 600)


@pytest.fixture(scope="module")
def config():
    config_str = """{
    "facility": "HFIR",
    "instrument": "CG1D",
    "ipts": "IPTS-1234",
    "name": "name for reconstructed ct scans",
    "workingdir": "/path/to/working/dir",
    "outputdir": "/tmp/imars3d/",
    "tasks": [{
            "name": "task1",
            "function": "imars3d.backend.io.data.load_data",
            "inputs": {
                "ct_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ct_scans/iron_man",
                "ob_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/ob/Oct29_2019/",
                "dc_dir": "tests/data/imars3d-data/HFIR/CG1D/IPTS-25777/raw/df/Oct29_2019/",
                "ct_fnmatch": "*.tiff",
                "ob_fnmatch": "*.tiff",
                "dc_fnmatch": "*.tiff"
            },
            "outputs": ["ct", "ob", "dc", "rot_angles"]
        },
        {
            "name": "task2.1",
            "function": "imars3d.backend.morph.crop.crop",
            "inputs": {
                "arrays": "ct",
                "crop_limit": [552, 1494, 771, 1296]
            },
            "outputs": ["ct"]
        },
        {
            "name": "task2.2",
            "function": "imars3d.backend.morph.crop.crop",
            "inputs": {
                "arrays": "ob",
                "crop_limit": [552, 1494, 771, 1296]
            },
            "outputs": ["ob"]
        },
        {
            "name": "task2.3",
            "function": "imars3d.backend.morph.crop.crop",
            "inputs": {
                "arrays": "dc",
                "crop_limit": [552, 1494, 771, 1296]
            },
            "outputs": ["dc"]
        },
        {
            "name": "task3",
            "function": "imars3d.backend.corrections.gamma_filter.gamma_filter",
            "inputs": {
                "arrays" : "ct"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task4",
            "function": "imars3d.backend.preparation.normalization.normalization",
            "inputs": {
                "arrays": "ct",
                "flats": "ob",
                "darks": "dc"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task5",
            "function": "imars3d.backend.corrections.denoise.denoise",
            "inputs": {
                "arrays": "ct"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task6",
            "function": "imars3d.backend.corrections.ring_removal.remove_ring_artifact",
            "inputs": {
                "arrays": "ct"
            },
            "outputs": ["ct"]
        },
        {
            "name": "task7",
            "function": "imars3d.backend.diagnostics.rotation.find_rotation_center",
            "inputs": {
                "arrays": "ct",
                "angles": "rot_angles",
                "in_degrees": true,
                "atol_deg": 0.5
            },
            "outputs": ["rot_center"]
        },
        {
            "name": "task8",
            "function": "imars3d.backend.reconstruction.recon",
            "inputs": {
                "arrays": "ct",
                "theta": "rot_angles",
                "center": "rot_center",
                "is_radians": false,
                "perform_minus_log": true
            },
            "outputs": ["result"]
        },
        {
            "name": "task9",
            "function": "imars3d.backend.io.data.save_data",
            "inputs": {
                "data": "result",
                "filename": "test",
                "outputdir" : "outputdir"
            },
            "outputs": []
        }
    ]
}"""
    return json.loads(config_str)


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
    def test_run(self, config):
        workflow = WorkflowEngineAuto(config)
        expected_slice_300 = np.load(str(DATA_DIR) + "/expected_slice_300.npy")
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
